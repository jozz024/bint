use amiibo::crypto::AmiiboDump;
use serde::Deserialize;
use serde::Serialize;
use hex;
use amiibo::ntag::NTagBase;

use super::rename::get_current_name;

#[derive(Default, Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Root {
    #[serde(rename = "FileVersion")]
    pub file_version: i64,
    #[serde(rename = "Name")]
    pub name: Option<String>,
    #[serde(rename = "TagUuid")]
    pub tag_uuid: String,
    #[serde(rename = "AmiiboId")]
    pub amiibo_id: String,
    #[serde(rename = "FirstWriteDate")]
    pub first_write_date: String,
    #[serde(rename = "LastWriteDate")]
    pub last_write_date: String,
    #[serde(rename = "WriteCounter")]
    pub write_counter: i64,
    #[serde(rename = "ApplicationAreas")]
    pub application_areas: Vec<ApplicationArea>,
}

#[derive(Default, Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ApplicationArea {
    #[serde(rename = "ApplicationAreaId")]
    pub application_area_id: i32,
    #[serde(rename = "ApplicationArea")]
    pub application_area: String,
}

fn generate_amiibo() -> AmiiboDump {
    let mut base_amiibo = [0_u8; 540].to_vec();

    // internal + static lock
    base_amiibo[0x09..0x0C].clone_from_slice(&hex::decode("480FE0").unwrap());
    // CC
    base_amiibo[0x0C..0x10].clone_from_slice(&hex::decode("F110FFEE").unwrap());
    // 0xA5 lol
    base_amiibo[0x10] = 0xA5;
    // write counter
    base_amiibo[0x11..0x13].clone_from_slice(&[0,0]);
    // settings
    base_amiibo[0x14..0x16].clone_from_slice(&hex::decode("3000").unwrap());
    // crc counter
    base_amiibo[0x16..0x18].clone_from_slice(&[0,0]);
    // last write date
    base_amiibo[0x1A..0x1C].clone_from_slice(&[0,0]);
    // owner mii
    base_amiibo[0xA0..0x100].clone_from_slice(&hex::decode("03 00 00 40 EB A5 21 1A E1 FD C7 59 D0 5A A5 4D 44 0D 56 BD 21 CA 00 00 00 00 4D 00 69 00 69 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 40 00 00 21 01 02 68 44 18 26 34 46 14 81 12 17 68 0D 00 00 29 00 52 48 50 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 14 6C".replace(' ', "")).unwrap());
    // application titleid
    base_amiibo[0x100..0x108].clone_from_slice(&hex::decode("01006A803016E000").unwrap());
    // 2nd write counter
    base_amiibo[0x108..0x10A].clone_from_slice(&[0,0]);
    // dynamic lock + rfui
    base_amiibo[0x208..0x20C].clone_from_slice(&hex::decode("01000FBD").unwrap());
    // cfg0 + cfg1
    base_amiibo[0x20c..0x214].clone_from_slice(&hex::decode("000000045F000000").unwrap());

    let mut dump = AmiiboDump::new(super::super::KEYS.clone(), base_amiibo);
    super::shuffle::shuffle_uid(&mut dump);
    dump
}

pub fn json_to_bin(json_contents: &str) -> AmiiboDump {
    let mut dump = generate_amiibo();

    let amiibo_json: Root = serde_json::from_str(json_contents).unwrap();
    if amiibo_json.name.is_some() {
        super::rename::rename(&mut dump, amiibo_json.name.unwrap());
    }
    else {
        super::rename::rename(&mut dump, "Ryujinx".to_string());
    }

    dump.data[84..92].clone_from_slice(&hex::decode(amiibo_json.amiibo_id).unwrap());

    if !amiibo_json.application_areas.is_empty() {
        dump.data[0x10a..0x10e].clone_from_slice(&amiibo_json.application_areas[0].application_area_id.to_be_bytes());
        dump.data[0x130..0x208].clone_from_slice(&base64::decode(amiibo_json.application_areas[0].application_area.as_str()).unwrap())
    }
    dump
}

pub fn bin_to_json(dump: &mut AmiiboDump) -> String {
    let amiibo_json = Root {
        file_version: 0,
        name: Some(get_current_name(dump)),
        tag_uuid: base64::encode(dump.get_uid_bin()),
        amiibo_id: hex::encode(&dump.data[84..92]),
        first_write_date: chrono::prelude::Local::now().format("%+").to_string(),
        last_write_date: chrono::prelude::Local::now().format("%+").to_string(),
        write_counter: 0,
        application_areas: vec![
            ApplicationArea {
                application_area_id: i32::from_str_radix(hex::encode(&dump.data[0x10a..0x10e]).as_str(), 16).unwrap(),
                application_area: base64::encode(&dump.data[0x130..0x208])
            }
        ]
    };

    serde_json::to_string_pretty(&amiibo_json).unwrap()
}