use amiibo::crypto::AmiiboDump;
use rand::Rng;
use amiibo::ntag::NTagBase;

pub fn shuffle_uid(dump: &mut AmiiboDump) {
    let mut serial_number = vec![0x04];
    let mut rng = rand::thread_rng();
    while serial_number.len() <= 7 {
        let temp_sn = rng.gen::<u8>();

        serial_number.append(&mut vec![temp_sn]);
    }
    dump.set_uid_bin(serial_number);
}