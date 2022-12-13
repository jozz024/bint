use amiibo::crypto::AmiiboDump;

use bitstream_io::{BigEndian, BitReader, BitRead};


pub fn bineval(dump: AmiiboDump) -> String {
    let mut output = String::new();

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
        output = format!("{}: {}\n", name, final_value) + &output;
    }
    output
}