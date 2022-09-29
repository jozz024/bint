use amiibo::crypto::AmiiboDump;
use amiibo::keys::AmiiboMasterKey;
use lazy_static::lazy_static;
use indexmap::IndexMap;

pub fn open_dump(mut data: Vec<u8>, keys: (AmiiboMasterKey, AmiiboMasterKey)) -> AmiiboDump{
    if 532 <= data.len() && data.len() <= 572 {
        match data.len().cmp(&540) {
            std::cmp::Ordering::Less => {
                while data.len() != 540 {
                    data.append(&mut vec![b'\x00'])
                }
                AmiiboDump::new(keys, data)
            }
            std::cmp::Ordering::Greater => {
                data = data[0..540].to_vec();
                AmiiboDump::new(keys, data)
            }
            std::cmp::Ordering::Equal => {
                AmiiboDump::new(keys, data)
            }
        }
    }
    else {
        panic!("Failed to parse amiibo!")
    }
}

fn calculate_u0(input: u32) -> [u32;0x100] {
	let p0: u32 = input | 0x80000000;


    let mut u0: [u32;0x100] = [0;0x100];

    for i in 0..256 {
		let mut t0: u32 = i;
		for _ in 0..8 {
			let b = t0 & 0x1;
			t0 >>= 1;
			if b > 0 {
				t0 ^= p0;
			}
		}
		u0[i as usize] = t0;
//		print!("{:02X} ", t0);
	}

    u0
}

fn default_u0() -> [u32;0x100] {
	calculate_u0(0xEDB88320)
}

fn calc0(buffer: &[u8], u:[u32;0x100], in_xor: u32, out_xor: u32) -> u32 {
	let mut t = in_xor;

	for k in buffer.iter() {
		let t8 = (t & 0xFF) as u8;
		let index = (k ^ t8) as usize;
		t = (t >> 0x8) ^ u[index];
	}

    t ^ out_xor
}

pub fn default_calc0(buffer: &[u8]) -> u32 {
	calc0(buffer, default_u0(), 0x0, 0xFFFFFFFF)
}

lazy_static!{
    pub static ref SECTIONS: IndexMap<String, u32> = IndexMap::from([
        ("Near".to_string(), 7),
        ("Offensive".to_string(), 7),
        ("Grounded".to_string(), 7),
        ("Attack Out Cliff".to_string(), 6),
        ("Dash".to_string(), 7),
        ("Return To Cliff".to_string(), 6),
        ("Air Offensive".to_string(), 6),
        ("Cliffer".to_string(), 6),
        ("Feint Master".to_string(), 7),
        ("Feint Counter".to_string(), 7),
        ("Feint Shooter".to_string(), 7),
        ("Catcher".to_string(), 7),
        ("100 Attacker".to_string(), 6),
        ("100 Keeper".to_string(), 6),
        ("Attack Cancel".to_string(), 6),
        ("Smash Holder".to_string(), 7),
        ("Dash Attacker".to_string(), 7),
        ("Critical Hitter".to_string(), 6),
        ("Meteor Master".to_string(), 6),
        ("Shield Master".to_string(), 7),
        ("Just Shield Master".to_string(), 6),
        ("Shield Catch Master".to_string(), 6),
        ("Item Collector".to_string(), 5),
        ("Item Throw to Target".to_string(), 5),
        ("Dragoon Collector".to_string(), 4),
        ("Smashball Collector".to_string(), 4),
        ("Hammer Collector".to_string(), 4),
        ("Special Flagger".to_string(), 4),
        ("Item Swinger".to_string(), 5),
        ("Homerun Batter".to_string(), 4),
        ("Club Swinger".to_string(), 4),
        ("Death Swinger".to_string(), 4),
        ("Item Shooter".to_string(), 5),
        ("Carrier Broker".to_string(), 5),
        ("Charger".to_string(), 5),
        ("Appeal".to_string(), 5),
        ("Fighter_1".to_string(), 7),
        ("Fighter_2".to_string(), 7),
        ("Fighter_3".to_string(), 7),
        ("Fighter_4".to_string(), 7),
        ("Fighter_5".to_string(), 7),
        ("Advantageous Fighter".to_string(), 7),
        ("Weaken Fighter".to_string(), 7),
        ("Revenge".to_string(), 7),
        ("Forward Tilt".to_string(), 10),
        ("Up Tilt".to_string(), 10),
        ("Down Tilt".to_string(), 10),
        ("Forward Smash".to_string(), 10),
        ("Up Smash".to_string(), 10),
        ("Down Smash".to_string(), 10),
        ("Neutral Special".to_string(), 10),
        ("Side Special".to_string(), 10),
        ("Up Special".to_string(), 10),
        ("Down Special".to_string(), 10),
        ("Forward Air".to_string(), 9),
        ("Back Air".to_string(), 9),
        ("Up Air".to_string(), 9),
        ("Down Air".to_string(), 9),
        ("Neutral Special Air".to_string(), 9),
        ("Side Special Air".to_string(), 9),
        ("Up Special Air".to_string(), 9),
        ("Down Special Air".to_string(), 9),
        ("Front Air Dodge".to_string(), 8),
        ("Back Air Dodge".to_string(), 8),
        ("APPEAL_HI".to_string(), 7),
        ("APPEAL_LW".to_string(), 7),
    ]);
}

lazy_static! {
    pub static ref PERSONALITY_NAMES: Vec<String> = vec!["Normal".to_string(),
    // def
    "Cautious".to_string(),
    "Realistic".to_string(),
    "Unflappable".to_string(),
    // agl
    "Light".to_string(),
    "Quick".to_string(),
    "Lightning Fast".to_string(),
    // ofn
    "Enthusiastic".to_string(),
    "Aggressive".to_string(),
    "Offensive".to_string(),
    // rsk
    "Reckless".to_string(),
    "Thrill Seeker".to_string(),
    "Daredevil".to_string(),
    // gen
    "Versatile".to_string(),
    "Tricky".to_string(),
    "Technician".to_string(),
    // ent
    "Show-Off".to_string(),
    "Flashy".to_string(),
    "Entertainer".to_string(),
    // cau
    "Cool".to_string(),
    "Logical".to_string(),
    "Sly".to_string(),
    // dyn
    "Laid Back".to_string(),
    "Wild".to_string(),
    "Lively".to_string()];
}