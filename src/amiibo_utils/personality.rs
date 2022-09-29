use std::collections::HashMap;

use amiibo::crypto::AmiiboDump;

use bitstream_io::{BigEndian, BitReader, BitRead};



use serde::Deserialize;
use serde::Serialize;


#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Root {
    pub def: PersonalityType,
    pub agl: PersonalityType,
    pub ofn: PersonalityType,
    pub rsk: PersonalityType,
    pub gen: PersonalityType,
    pub ent: PersonalityType,
    pub cau: PersonalityType,
    #[serde(rename = "dyn")]
    pub dyn_: PersonalityType,
}
impl IntoIterator for Root {
    type Item = PersonalityType;
    type IntoIter = std::array::IntoIter<PersonalityType, 8>;

    fn into_iter(self) -> Self::IntoIter {
        std::iter::IntoIterator::into_iter([self.def, self.agl, self.ofn, self.rsk, self.gen, self.ent, self.cau, self.dyn_])
    }
}
#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PersonalityType {
    pub index: i64,
    pub scores: Vec<Score>,
    pub tiers: Vec<Tier>,
    #[serde(rename = "necessary_param")]
    pub necessary_param: Option<String>,
    #[serde(rename = "necessary_min")]
    pub necessary_min: f64,
    #[serde(rename = "necessary_flip")]
    pub necessary_flip: bool,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Score {
    pub param: String,
    #[serde(rename = "min_1")]
    pub min_1: f64,
    #[serde(rename = "point_1")]
    pub point_1: i64,
    #[serde(rename = "min_2")]
    pub min_2: f64,
    #[serde(rename = "point_2")]
    pub point_2: i64,
    pub flip: bool,
}

#[derive(Default, Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Tier {
    pub points: i64,
    pub personality: i64,
}

fn decode_behavior_params(dump: &AmiiboDump) -> HashMap<String, f32> {
    let mut params: HashMap<String, f32> = HashMap::new();

    let mut param_defs = crate::utils::SECTIONS.clone();
    param_defs.reverse();

    let mut training_data = dump.data[0x1BC..0x1F6].to_vec();
    training_data.reverse();
    let mut stream = BitReader::endian(&training_data[..], BigEndian);

    for (name, size) in param_defs.iter() {
        let size = *size;
        let val = stream.read::<u32>(size).unwrap();

        let val_max = (1 << size) - 1;

        let final_value = (val as f32 / val_max as f32) * 100.0;
        params.insert(name.to_lowercase().to_string(), final_value);
    }
    params
}

fn scale_value(_param: String, value: f32, flip: bool) -> f32{
    // some of the "directional weight" parameters have different defaults defined in the code but none of them are ever used here so lol
    let default: f32 = 50.0;
    let scaled = if flip {
        (default - value) / default
    }
    else {
        (value - default) / default
    };
    // since we rescale to range from -1.0 to 1.0, this means values below halfway are meaningless lol
    f32::max(0.0, f32::min(1.0, scaled))
}

fn calculate_group_score(params: &HashMap<String, f32>, group: &PersonalityType) -> i64 {
    let mut score = 0;
    for param_data in group.scores.iter().clone() {
        let name = param_data.param.as_str().replace('_', " ");
        let name = name.as_str();
        let value = scale_value(name.to_string(), params[&name.to_string()], param_data.flip) as f64;

        if value >= param_data.min_1 {
            score += param_data.point_1
        }
        if value >= param_data.min_2 {
            score += param_data.point_2
        }
    }
    score
}

fn meets_group_necessary_requirements(params: &HashMap<String, f32>, group: &PersonalityType) -> bool {
    let name = group.necessary_param.as_ref().unwrap_or(&"None".to_string()).replace('_', " ");
    let name = name.as_str();

    if name == "None" {
        return true
    }
    let value = scale_value(name.to_string(), params[&name.to_string()], group.necessary_flip) as f64;
    value >= group.necessary_min
}

fn get_personality_tier(group: PersonalityType, score: i64) -> i64 {
    let mut winner = 0;
    for tier in group.tiers.iter().clone() {
        if score >= tier.points {
            winner = tier.personality
        }
    }
    winner
}
fn get_highest_hashmap_value(a_hash_map: &HashMap<i64, PersonalityType>) -> (i64, PersonalityType) {
    (a_hash_map.clone().into_keys().max().unwrap(), a_hash_map[&a_hash_map.clone().into_keys().max().unwrap()].clone())
}

fn calculate_personality_raw(params: HashMap<String, f32>) -> i64 {
    let mut group_scores:HashMap<i64, PersonalityType> = HashMap::new();
    let group_json = std::fs::read_to_string("./personality_data.json").unwrap();
    let groups_data: Root = serde_json::from_str(group_json.as_str()).unwrap();
    for group_data in groups_data {
        if !meets_group_necessary_requirements(&params, &group_data) {
            continue
        }
        let score = calculate_group_score(&params, &group_data);

        // using numeric index as a tiebreaker here
        group_scores.insert(score, group_data.clone());
    }
    if group_scores.is_empty() {
        // if no groups are eligible, we're Normal
        return 0
    }
    // find the best group!
    let (winner_score, winner_group) = get_highest_hashmap_value(&group_scores);
    get_personality_tier(winner_group, winner_score)
}

pub fn calculate_personality(dump: &AmiiboDump) -> String {
    let params = decode_behavior_params(dump);
    let personality = calculate_personality_raw(params);

    crate::utils::PERSONALITY_NAMES[personality as usize].clone()
}
