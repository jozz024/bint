use amiibo::crypto::AmiiboDump;
use utf16string::{BE, WString};

pub fn rename(dump: &mut AmiiboDump, new_name: String) {
    let new_name: WString<BE> = WString::from(&new_name);

    let mut new_name_bytes = new_name.as_bytes().to_vec();

    while new_name_bytes.len() < 20 {
        new_name_bytes.append(&mut b"\x00".to_vec())
    }

    assert!(new_name_bytes.len() == 20, "amiibo name too big!");

    dump.data[0x020..0x034].clone_from_slice(&new_name_bytes[..]);
}

pub fn get_current_name(dump: &mut AmiiboDump) -> String {
    let name: WString<BE> = WString::from_utf16(dump.data[0x020..0x034].to_vec()).unwrap();
    name.as_wstr().to_string().trim_matches(char::from(0)).to_string()
}