

mod amiibo_utils;
mod utils;
use amiibo::keys::AmiiboMasterKey;
use serenity::model::prelude::Activity;
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use lazy_static::lazy_static;
use serenity::async_trait;
use serenity::client::bridge::gateway::ShardManager;
use serenity::framework::standard::buckets::LimitedFor;
use serenity::framework::standard::macros::{command, group, help, hook};
use serenity::framework::standard::{
    help_commands,
    Args,
    CommandGroup,
    CommandResult,
    DispatchError,
    HelpOptions,
    StandardFramework,
};
use serenity::http::Http;
use serenity::model::channel::Message;
use serenity::model::gateway::{GatewayIntents, Ready};
use serenity::model::id::UserId;
use serenity::prelude::*;
use tokio::sync::Mutex;

lazy_static! {
    pub static ref KEYS: (AmiiboMasterKey, AmiiboMasterKey) = AmiiboMasterKey::from_separate_hex( "1D 16 4B 37 5B 72 A5 57 28 B9 1D 64 B6 A3 C2 05 75 6E 66 69 78 65 64 20 69 6E 66 6F 73 00 00 0E DB 4B 9E 3F 45 27 8F 39 7E FF 9B 4F B9 93 00 00 04 49 17 DC 76 B4 96 40 D6 F8 39 39 96 0F AE D4 EF 39 2F AA B2 14 28 AA 21 FB 54 E5 45 05 47 66".replace(' ', "").as_str(), "7F752D2873A20017FEF85C0575904B6D6C6F636B656420736563726574000010FDC8A07694B89E4C47D37DE8CE5C74C1044917DC76B49640D6F83939960FAED4EF392FAAB21428AA21FB54E545054766");
}
// A container type is created for inserting into the Client's `data`, which
// allows for data to be accessible across all events and framework commands, or
// anywhere else that has a copy of the `data` Arc.
struct ShardManagerContainer;

impl TypeMapKey for ShardManagerContainer {
    type Value = Arc<Mutex<ShardManager>>;
}

struct CommandCounter;

impl TypeMapKey for CommandCounter {
    type Value = HashMap<String, u64>;
}

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: Ready) {
        let activity = Activity::listening("Amiibo modification bot.");
        let status = serenity::model::user::OnlineStatus::Idle;
        ctx.set_presence(Some(activity), status).await;
        println!("{} is connected!", ready.user.name);
    }
}

#[group]
#[commands(evaluate, transplant,set_spirits, personality, rename, shufflesn, json_to_bin, bin_to_json)]
struct General;


// The framework provides two built-in help commands for you to use.
// But you can also make your own customized help command that forwards
// to the behaviour of either of them.
#[help]
// This replaces the information that a user can pass
// a command-name as argument to gain specific information about it.
#[individual_command_tip = "Hello! こんにちは！Hola! Bonjour! 您好! 안녕하세요~\n\n\
If you want more information about a specific command, just pass the command as argument."]
// Some arguments require a `{}` in order to replace it with contextual information.
// In this case our `{}` refers to a command's name.
#[command_not_found_text = "Could not find: `{}`."]
// Define the maximum Levenshtein-distance between a searched command-name
// and commands. If the distance is lower than or equal the set distance,
// it will be displayed as a suggestion.
// Setting the distance to 0 will disable suggestions.
#[max_levenshtein_distance(3)]
// When you use sub-groups, Serenity will use the `indention_prefix` to indicate
// how deeply an item is indented.
// The default value is "-", it will be changed to "+".
#[indention_prefix = "+"]
// On another note, you can set up the help-menu-filter-behaviour.
// Here are all possible settings shown on all possible options.
// First case is if a user lacks permissions for a command, we can hide the command.
#[lacking_permissions = "Hide"]
// If the user is nothing but lacking a certain role, we just display it hence our variant is `Nothing`.
#[lacking_role = "Nothing"]
// The last `enum`-variant is `Strike`, which ~~strikes~~ a command.
#[wrong_channel = "Strike"]
// Serenity will automatically analyse and generate a hint/tip explaining the possible
// cases of ~~strikethrough-commands~~, but only if
// `strikethrough_commands_tip_in_{dm, guild}` aren't specified.
// If you pass in a value, it will be displayed instead.
async fn my_help(
    context: &Context,
    msg: &Message,
    args: Args,
    help_options: &'static HelpOptions,
    groups: &[&'static CommandGroup],
    owners: HashSet<UserId>,
) -> CommandResult {
    let _ = help_commands::with_embeds(context, msg, args, help_options, groups, owners).await;
    Ok(())
}

#[hook]
async fn before(ctx: &Context, msg: &Message, command_name: &str) -> bool {
    println!("Got command '{}' by user '{}'", command_name, msg.author.name);

    // Increment the number of times this command has been run once. If
    // the command's name does not exist in the counter, add a default
    // value of 0.
    let mut data = ctx.data.write().await;
    let counter = data.get_mut::<CommandCounter>().expect("Expected CommandCounter in TypeMap.");
    let entry = counter.entry(command_name.to_string()).or_insert(0);
    *entry += 1;

    true // if `before` returns false, command processing doesn't happen.
}

#[hook]
async fn after(_ctx: &Context, _msg: &Message, command_name: &str, command_result: CommandResult) {
    match command_result {
        Ok(()) => println!("Processed command '{}'", command_name),
        Err(why) => println!("Command '{}' returned error {:?}", command_name, why),
    }
}

#[hook]
async fn unknown_command(_ctx: &Context, _msg: &Message, unknown_command_name: &str) {
    println!("Could not find command named '{}'", unknown_command_name);
}

#[hook]
async fn normal_message(_ctx: &Context, msg: &Message) {
    println!("Message is not a command '{}'", msg.content);
}

#[hook]
async fn delay_action(ctx: &Context, msg: &Message) {
    // You may want to handle a Discord rate limit if this fails.
    let _ = msg.react(ctx, '⏱').await;
}

#[hook]
async fn dispatch_error(ctx: &Context, msg: &Message, error: DispatchError, _command_name: &str) {
    if let DispatchError::Ratelimited(info) = error {
        // We notify them only once.
        if info.is_first_try {
            let _ = msg
                .channel_id
                .say(&ctx.http, &format!("Try this again in {} seconds.", info.as_secs()))
                .await;
        }
    }
}


#[tokio::main]
async fn main() {
    // Configure the client with your Discord bot token in the environment.
    let token = "TOKEN".to_string();

    let http = Http::new(&token);

    // We will fetch your bot's owners and id
    let (owners, bot_id) = match http.get_current_application_info().await {
        Ok(info) => {
            let mut owners = HashSet::new();
            if let Some(team) = info.team {
                owners.insert(team.owner_user_id);
            } else {
                owners.insert(info.owner.id);
            }
            match http.get_current_user().await {
                Ok(bot_id) => (owners, bot_id.id),
                Err(why) => panic!("Could not access the bot id: {:?}", why),
            }
        },
        Err(why) => panic!("Could not access application info: {:?}", why),
    };

    let framework = StandardFramework::new()
        .configure(|c| c
                   .with_whitespace(true)
                   .on_mention(Some(bot_id))
                   .prefix("!")
                   // In this case, if "," would be first, a message would never
                   // be delimited at ", ", forcing you to trim your arguments if you
                   // want to avoid whitespaces at the start of each.
                   .delimiters(vec![", ", ","])
                   // Sets the bot's owners. These will be used for commands that
                   // are owners only.
                   .owners(owners))

    // Set a function to be called prior to each command execution. This
    // provides the context of the command, the message that was received,
    // and the full name of the command that will be called.
    //
    // Avoid using this to determine whether a specific command should be
    // executed. Instead, prefer using the `#[check]` macro which
    // gives you this functionality.
    //
    // **Note**: Async closures are unstable, you may use them in your
    // application if you are fine using nightly Rust.
    // If not, we need to provide the function identifiers to the
    // hook-functions (before, after, normal, ...).
        .before(before)
    // Similar to `before`, except will be called directly _after_
    // command execution.
        .after(after)
    // Set a function that's called whenever an attempted command-call's
    // command could not be found.
        .unrecognised_command(unknown_command)
    // Set a function that's called whenever a message is not a command.
        .normal_message(normal_message)
    // Set a function that's called whenever a command's execution didn't complete for one
    // reason or another. For example, when a user has exceeded a rate-limit or a command
    // can only be performed by the bot owner.
        .on_dispatch_error(dispatch_error)
    // Can't be used more than once per 5 seconds:
        .bucket("emoji", |b| b.delay(5)).await
    // Can't be used more than 2 times per 30 seconds, with a 5 second delay applying per channel.
    // Optionally `await_ratelimits` will delay until the command can be executed instead of
    // cancelling the command invocation.
        .bucket("complicated", |b| b.limit(2).time_span(30).delay(5)
            // The target each bucket will apply to.
            .limit_for(LimitedFor::Channel)
            // The maximum amount of command invocations that can be delayed per target.
            // Setting this to 0 (default) will never await/delay commands and cancel the invocation.
            .await_ratelimits(1)
            // A function to call when a rate limit leads to a delay.
            .delay_action(delay_action)).await
    // The `#[group]` macro generates `static` instances of the options set for the group.
    // They're made in the pattern: `#name_GROUP` for the group instance and `#name_GROUP_OPTIONS`.
    // #name is turned all uppercase
        .help(&MY_HELP)
        .group(&GENERAL_GROUP);

    // For this example to run properly, the "Presence Intent" and "Server Members Intent"
    // options need to be enabled.
    // These are needed so the `required_permissions` macro works on the commands that need to
    // use it.
    // You will need to enable these 2 options on the bot application, and possibly wait up to 5
    // minutes.
    let intents = GatewayIntents::all();
    let mut client = Client::builder(&token, intents)
        .event_handler(Handler)
        .framework(framework)
        .type_map_insert::<CommandCounter>(HashMap::default())
        .await
        .expect("Err creating client");

    {
        let mut data = client.data.write().await;
        data.insert::<ShardManagerContainer>(Arc::clone(&client.shard_manager));
    }

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}



#[command]
#[only_in("dm")]
#[aliases("bineval")]
async fn evaluate(ctx: &Context, msg: &Message, _args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }
    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();
    let eval = amiibo_utils::evaluate::bineval(dump);

    msg.reply(&ctx.http, format!("```{}```", eval)).await?;
    Ok(())

}

#[command]
#[only_in("dm")]
async fn transplant(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }

    if args.is_empty() {
        msg.reply(&ctx.http, "No character specified!").await?;
        return Ok(())
    }

    let character = args.single::<String>().unwrap();

    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();

    amiibo_utils::transplant::transplant(character.as_str(), &mut dump);

    dump.lock();
    let filename =  msg.attachments[0].filename.clone();
    let f = [(&dump.data[..], filename.as_str())];
    msg.channel_id.send_message(&ctx.http, |m| {
        m.content("file sent!");
        m.files(f);
        m
    }).await.unwrap();

    Ok(())
}

#[command]
#[only_in("dm")]
#[aliases("setspirits")]
async fn set_spirits(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }

    if args.is_empty() {
        msg.reply(&ctx.http, "No spirits specified!").await?;
        return Ok(())
    }
    let mut spirits = Vec::new();
    let attack = args.current().unwrap().parse::<u16>().unwrap();
    args.advance();
    let defense = args.current().unwrap().parse::<u16>().unwrap();
    args.advance();
    for spirit in args.iter::<String>() {
        let spirit = spirit.unwrap().clone().to_owned();
        let spirit = spirit.as_str().to_owned();
        spirits.append(&mut vec![spirit]);
    }

    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();

    amiibo_utils::spirits::set_spirits(&mut dump, attack, defense, spirits);

    let mut application_area = dump.data[308..520].to_vec();

    let mut checksum = utils::default_calc0(&application_area).to_le_bytes().to_vec();

    checksum.append(&mut application_area);

    dump.data[304..520].clone_from_slice(&checksum);

    dump.lock();    
    let filename =  msg.attachments[0].filename.clone();
    let f = [(&dump.data[..], filename.as_str())];
    msg.channel_id.send_message(&ctx.http, |m| {
        m.content("file sent!");
        m.files(f);
        m
    }).await.unwrap();

    Ok(())
}

#[command]
#[only_in("dm")]
#[aliases("personalitycalc")]
async fn personality(ctx: &Context, msg: &Message, _args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }
    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();
    let personality = amiibo_utils::personality::calculate_personality(&dump);

    msg.reply(&ctx.http, format!("Amiibo's personality is: \n```{}```", personality)).await?;
    Ok(())
}

#[command]
#[only_in("dm")]
async fn rename(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }

    if args.is_empty() {
        msg.reply(&ctx.http, "No name specified!").await?;
        return Ok(())
    }

    let name = args.single::<String>().unwrap();

    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();

    amiibo_utils::rename::rename(&mut dump, name);

    dump.lock();
    let filename =  msg.attachments[0].filename.clone();
    let f = [(&dump.data[..], filename.as_str())];
    msg.channel_id.send_message(&ctx.http, |m| {
        m.content("file sent!");
        m.files(f);
        m
    }).await.unwrap();

    Ok(())
}

#[command]
#[only_in("dm")]
async fn shufflesn(ctx: &Context, msg: &Message, _args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }

    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();

    amiibo_utils::shuffle::shuffle_uid(&mut dump);

    dump.lock();
    let filename =  msg.attachments[0].filename.clone();
    let f = [(&dump.data[..], filename.as_str())];
    msg.channel_id.send_message(&ctx.http, |m| {
        m.content("file sent!");
        m.files(f);
        m
    }).await.unwrap();

    Ok(())
}

#[command]
#[only_in("dm")]
#[aliases("ryu2bin")]
async fn json_to_bin(ctx: &Context, msg: &Message, _args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }

    let json = String::from_utf8(msg.attachments[0].download().await.unwrap()).unwrap();

    let mut dump = amiibo_utils::ryujinx::json_to_bin(json.as_str());

    dump.lock();
    let filename =  msg.attachments[0].filename.clone().replace(".json", ".bin");
    let f = [(&dump.data[..], filename.as_str())];
    msg.channel_id.send_message(&ctx.http, |m| {
        m.content("file sent!");
        m.files(f);
        m
    }).await.unwrap();

    Ok(())
}

#[command]
#[only_in("dm")]
#[aliases("bin2ryu")]
async fn bin_to_json(ctx: &Context, msg: &Message, _args: Args) -> CommandResult {
    if msg.attachments.is_empty() {
        msg.reply(&ctx.http, "No file was attached!").await?;
        return Ok(())
    }

    let bin = msg.attachments[0].download().await.unwrap();

    let mut dump = utils::open_dump(bin, KEYS.clone());
    dump.unlock();

    let amiibo_json = amiibo_utils::ryujinx::bin_to_json(&mut dump);
    let filename =  msg.attachments[0].filename.clone().replace(".bin", ".json");
    let f = [(amiibo_json.as_bytes(), filename.as_str())];
    msg.channel_id.send_message(&ctx.http, |m| {
        m.content("file sent!");
        m.files(f);
        m
    }).await.unwrap();

    Ok(())
}