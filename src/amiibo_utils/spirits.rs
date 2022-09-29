

use amiibo::crypto::AmiiboDump;
use serde::Deserialize;
use serde::Serialize;
use serde_json::Value;

type SpiritSkillList = Vec<SpiritSkill>;

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SpiritSkill {
    pub description: Value,
    pub id: u8,
    pub name: String,
    pub notes: Value,
    #[serde(rename = "slot_cost")]
    pub slot_cost: i64,
    pub tags: Vec<String>,
    #[serde(rename = "type")]
    pub type_field: String,
}

fn parse_spirit_skill_json(json: &str) -> SpiritSkillList {
    let spirits: SpiritSkillList = serde_json::from_str(json).unwrap();
    spirits
}

pub fn set_spirits(dump: &mut AmiiboDump, attack: u16, defense: u16, mut skills: Vec<String>) {
    let spirit_skill_file = std::fs::read_to_string("./spirits.json");
    let spirits = parse_spirit_skill_json(spirit_skill_file.unwrap().as_str());


    let mut spirit_skills: SpiritSkillList = Vec::new();

    while skills.len() < 3 {
        skills.append(&mut vec!["none".to_string()]);
    }

    for skill_name in skills {
        let spirit = get_spirit_from_name(skill_name.as_str(), &spirits);
        spirit_skills.append(&mut vec![spirit.unwrap_or_else(|| get_spirit_from_name("none", &spirits).unwrap())])
    }
    let is_valid = validate_loadout(attack, defense, &spirit_skills);
    if is_valid {
        dump.data[0x1A4..0x1A6].clone_from_slice(&attack.to_le_bytes());
        dump.data[0x1A6..0x1A8].clone_from_slice(&defense.to_le_bytes());
        dump.data[0x140] = spirit_skills[0].id;
        dump.data[0x141] = spirit_skills[1].id;
        dump.data[0x142] = spirit_skills[2].id;
    }
}

fn get_spirit_from_name(name: &str, spirits: &SpiritSkillList) -> Option<SpiritSkill> {
    for spirit in spirits {
        if spirit.name.to_lowercase().as_str() == name {
            return Some(spirit.to_owned())
        }
    }
    None
}

fn validate_loadout(attack: u16, defense: u16, spirits: &SpiritSkillList) -> bool {
    let slots_filled =
        spirits[0].slot_cost +
        spirits[1].slot_cost +
        spirits[2].slot_cost;

    let mut max_stats: u16 = 5000;

    if slots_filled == 1 {
        max_stats -= 300
    }

    if slots_filled == 2 {
        max_stats -= 500
    }

    if slots_filled == 3 {
        max_stats -= 800
    }

    attack + defense <= max_stats
}