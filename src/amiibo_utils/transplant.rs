use amiibo::crypto::AmiiboDump;
use serde::Deserialize;
use serde::Serialize;

#[derive(Default, Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Root {
    pub characters: Vec<Character>,
}

#[derive(Default, Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Character {
    pub name: String,
    pub id: String,
}


pub fn transplant(character_name: &str, dump: &mut AmiiboDump) {
    let raw_json = std::fs::read_to_string("./characters.json").unwrap();

    let characters: Root = serde_json::from_str(raw_json.as_str()).unwrap();

    for character in characters.characters {
        if character.name == *character_name {
            dump.data[84..92].copy_from_slice(&hex::decode(character.id).unwrap());
        }
    }
}