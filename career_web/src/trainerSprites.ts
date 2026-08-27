import type { CareerCatalog, CareerRun } from "./types";

export interface TrainerSpriteOption {
  id: string;
  label: string;
  region: string;
}

export interface TrainerSpriteStorageEntry {
  key: string;
  sprite: string;
}

const TRAINER_SPRITE_BASE = "https://play.pokemonshowdown.com/sprites/trainers";
export const DEFAULT_TRAINER_SPRITE = "red";

// Pokemon Showdown's public trainer whitelist. Keeping IDs as text is cheap: the
// picker renders only the selected image, so expanding the catalog does not turn
// the creation screen into hundreds of simultaneous sprite requests.
const SHOWDOWN_ARCHIVE = `aaron acetrainercouple-gen3 acetrainercouple acetrainerf-gen1 acetrainerf-gen1rb acetrainerf-gen2 acetrainerf-gen3 acetrainerf-gen3rs acetrainerf-gen4dp acetrainerf-gen4 acetrainerf acetrainer-gen1 acetrainer-gen1rb acetrainer-gen2 acetrainer-gen3jp acetrainer-gen3 acetrainer-gen3rs acetrainer-gen4dp acetrainer-gen4 acetrainer acetrainersnowf acetrainersnow agatha-gen1 agatha-gen1rb agatha-gen3 alder anabel-gen3 archer archie-gen3 argenta ariana aromalady-gen3 aromalady-gen3rs aromalady artist-gen4 artist ash backersf backers backpackerf backpacker baker barry battlegirl-gen3 battlegirl-gen4 battlegirl beauty-gen1 beauty-gen1rb beauty-gen2jp beauty-gen2 beauty-gen3 beauty-gen3rs beauty-gen4dp beauty-gen5bw2 beauty bellelba bellepa benga bertha bianca biker-gen1 biker-gen1rb biker-gen2 biker-gen3 biker-gen4 biker bill-gen3 birch-gen3 birdkeeper-gen1 birdkeeper-gen1rb birdkeeper-gen2 birdkeeper-gen3 birdkeeper-gen3rs birdkeeper-gen4dp birdkeeper blackbelt-gen1 blackbelt-gen1rb blackbelt-gen2 blackbelt-gen3 blackbelt-gen3rs blackbelt-gen4dp blackbelt-gen4 blackbelt blaine-gen1 blaine-gen1rb blaine-gen2 blaine-gen3 blaine blue-gen1champion blue-gen1 blue-gen1rbchampion blue-gen1rb blue-gen1rbtwo blue-gen1two blue-gen2 blue-gen3champion blue-gen3 blue-gen3two blue boarder-gen2 boarder brandon-gen3 brawly-gen3 brawly breederf breeder brendan-gen3 brendan-gen3rs brock-gen1 brock-gen1rb brock-gen2 brock-gen3 brock bruno-gen1 bruno-gen1rb bruno-gen2 bruno-gen3 bruno brycenman brycen buck bugcatcher-gen1 bugcatcher-gen1rb bugcatcher-gen2 bugcatcher-gen3 bugcatcher-gen3rs bugcatcher bugmaniac-gen3 bugsy-gen2 bugsy burgh burglar-gen1 burglar-gen1rb burglar-gen2 burglar-gen3 burglar byron caitlin cameraman camper-gen2 camper-gen3 camper-gen3rs camper candice channeler-gen1 channeler-gen1rb channeler-gen3 cheren-gen5bw2 cheren cheryl chili chuck-gen2 chuck cilan clair-gen2 clair clay clemont clerk-boss clerkf clerk clown collector-gen3 collector colress courtney-gen3 cowgirl crasherwake cress crushgirl-gen3 crushkin-gen3 cueball-gen1 cueball-gen1rb cueball-gen3 cyclistf-gen4 cyclistf cyclist-gen4 cyclist cynthia-gen4 cynthia cyrus dahlia dancer darach dawn-gen4pt dawn depotagent doctor doubleteam dragontamer-gen3 dragontamer drake-gen3 drayden elesa-gen5bw2 elesa emmet engineer-gen1 engineer-gen1rb engineer-gen3 erika-gen1 erika-gen1rb erika-gen2 erika-gen3 erika ethan-gen2c ethan-gen2 ethan eusine-gen2 eusine expertf-gen3 expertm-gen3 falkner-gen2 falkner fantina firebreather-gen2 firebreather fisherman-gen1 fisherman-gen1rb fisherman-gen2jp fisherman-gen3 fisherman-gen3rs fisherman-gen4 fisherman flannery-gen3 flannery flint galacticgruntf galacticgrunt gambler-gen1 gambler-gen1rb gambler gamer-gen3 gardenia gentleman-gen1 gentleman-gen1rb gentleman-gen3 gentleman-gen3rs gentleman-gen4dp gentleman-gen4 gentleman ghetsis-gen5bw ghetsis giovanni-gen1 giovanni-gen1rb giovanni-gen3 giovanni glacia-gen3 greta-gen3 grimsley guitarist-gen3 guitarist-gen4 guitarist harlequin hexmaniac-gen3jp hexmaniac-gen3 hiker-gen1 hiker-gen1rb hiker-gen3 hiker-gen3rs hiker-gen4 hiker hilbert-dueldisk hilbert hilda-dueldisk hilda hooligans hoopster hugh idol infielder ingo interviewer-gen3 interviewers iris-gen5bw2 iris janine-gen2 janine janitor jasmine-gen2 jasmine jessiejames-gen1 jogger jrtrainerf-gen1 jrtrainerf-gen1rb jrtrainerm-gen1 jrtrainerm-gen1rb juan-gen3 juan juggler-gen1 juggler-gen1rb juggler-gen2 juggler-gen3 juggler jupiter karen-gen2 karen kimonogirl kindler-gen3 koga-gen1 koga-gen1rb koga-gen3 koga kris-gen2 lady-gen3 lady-gen3rs lady-gen4 lady lance-gen1 lance-gen1rb lance-gen2 lance-gen3 lance lass-gen1 lass-gen1rb lass-gen2 lass-gen3 lass-gen3rs lass-gen4dp lass-gen4 lass leaf-gen3 lenora linebacker li liza lorelei-gen1 lorelei-gen1rb lorelei-gen3 ltsurge-gen1 ltsurge-gen1rb ltsurge-gen2 ltsurge-gen3 ltsurge lucas-gen4pt lucas lucian lucy-gen3 lyra madame-gen4dp madame-gen4 madame maid marley marlon marshal mars matt-gen3 maxie-gen3 may-gen3 may-gen3rs maylene medium-gen2jp medium mira misty-gen1 misty-gen1rb misty-gen3 misty morty-gen2 morty mrfuji-gen3 musician nate ninjaboy-gen3 ninjaboy noland-gen3 norman-gen3 norman n nurse nurseryaide oak-gen1 oak-gen1rb oak-gen3 oldcouple-gen3 painter-gen3 palmer parasollady-gen3 parasollady-gen4 parasollady petrel phoebe-gen3 picnicker-gen2 picnicker-gen3 picnicker-gen3rs picnicker pilot plasmagruntf-gen5bw plasmagruntf plasmagrunt-gen5bw plasmagrunt pokefanf-gen2 pokefanf-gen3 pokefanf-gen4 pokefanf pokefan-gen3 pokefan-gen4 pokefan pokekid pokemaniac-gen1 pokemaniac-gen1rb pokemaniac-gen3 pokemaniac-gen3rs pokemaniac pokemonbreederf-gen3 pokemonbreederf pokemonbreeder-gen3 pokemonbreederm-gen3 pokemonbreeder pokemonrangerf-gen3 pokemonrangerf-gen3rs pokemonrangerf-gen4 pokemonrangerf pokemonranger-gen3 pokemonranger-gen3rs pokemonranger-gen4 pokemonranger policeman-gen4 policeman preschoolerf preschooler proton pryce psychicf-gen3 psychicf-gen3rs psychicf-gen4 psychicfjp-gen3 psychicf psychic-gen1 psychic-gen1rb psychic-gen3 psychic-gen3rs psychic-gen4 psychic rancher red-gen1main red-gen1 red-gen1rb red-gen1title red-gen3 red reporter richboy-gen3 richboy-gen4 richboy riley roark rocker-gen1 rocker-gen1rb rocker-gen3 rocket-gen1 rocket-gen1rb rocketgruntf-gen2 rocketgruntf rocketgruntm-gen2 rocketgrunt rood rosa roughneck-gen4 roughneck roxanne-gen3 roxanne roxie ruinmaniac-gen3 ruinmaniac-gen3rs ruinmaniac sabrina-gen1 sabrina-gen1rb sabrina-gen2 sabrina-gen3 sabrina sage-gen2 sagejp-gen2 sage sailor-gen1 sailor-gen1rb sailor-gen2 sailor-gen3jp sailor-gen3 sailor-gen3rs sailor saturn schoolboy-gen2 schoolkidf-gen3 schoolkidf-gen4 schoolkidf schoolkid-gen4dp schoolkid-gen4 schoolkidm-gen3 schoolkid scientistf scientist-gen1 scientist-gen1rb scientist-gen2 scientist-gen3 scientist-gen4dp scientist-gen4 scientist shadowtriad shauntal shelly-gen3 sidney-gen3 silver-gen2kanto silver-gen2 silver sisandbro-gen3 sisandbro-gen3rs sisandbro skierf-gen4dp skierf skier-gen2 skier skyla smasher spenser-gen3 srandjr-gen3 steven-gen3 steven striker supernerd-gen1 supernerd-gen1rb supernerd-gen2 supernerd-gen3 supernerd swimmerf-gen2 swimmerf-gen3 swimmerf-gen3rs swimmerf-gen4dp swimmerf-gen4 swimmerfjp-gen2 swimmerf swimmer-gen1 swimmer-gen1rb swimmer-gen4dp swimmer-gen4 swimmerm-gen2 swimmerm-gen3 swimmerm-gen3rs swimmer tabitha-gen3 tamer-gen1 tamer-gen1rb tamer-gen3 tateandliza-gen3 tate teacher-gen2 teacher teamaquabeta-gen3 teamaquagruntf-gen3 teamaquagruntm-gen3 teammagmagruntf-gen3 teammagmagruntm-gen3 teamrocketgruntf-gen3 teamrocketgruntm-gen3 teamrocket thorton triathletebikerf-gen3 triathletebikerm-gen3 triathleterunnerf-gen3 triathleterunnerm-gen3 triathleteswimmerf-gen3 triathleteswimmerm-gen3 tuberf-gen3 tuberf-gen3rs tuberf tuber-gen3 tuber tucker-gen3 twins-gen2 twins-gen3 twins-gen3rs twins-gen4dp twins-gen4 twins unknownf unknown veteranf veteran-gen4 veteran volkner waiter-gen4dp waiter-gen4 waiter waitress-gen4 waitress wallace-gen3 wallace-gen3rs wallace wally-gen3 wally wattson-gen3 wattson whitney-gen2 whitney will-gen2 will winona-gen3 winona worker-gen4 workerice worker yellow youngcouple-gen3 youngcouple-gen3rs youngcouple-gen4dp youngcouple youngster-gen1 youngster-gen1rb youngster-gen2 youngster-gen3 youngster-gen3rs youngster-gen4 youngster zinnia zinzolin`;

// Canonical game characters added to Showdown after the older whitelist snapshot.
// IDs below are stable names from the current Showdown trainer directory.
const MODERN_CHARACTER_IDS = `acerola adaman akari allister amarys anabel anthe arven-s atticus avery bede bede-leader bea brassius briar burnet calem carmine carmine-festival chase cheren clavell-s cogita colress courtney crispin diantha elio eri florian-s gaeric geeta gladion gloria gordie grant grusha guzma hala hapu hau hop iono irida juliana-s kabu kahili kamado katy kiawe kieran kieran-champion klara kofu korrina kukui lana leon lillie lusamine mallow marnie melony milo molayne mustard nanu nemona-s nessa oleana olivia opal penny peonia peony perrin piers plumeria raihan rika rose ryme selene serena shauna siebold sonia sophocles sycamore trace tulip valerie victor viola volo wulfric`;

const ARCHIVE_IDS = Array.from(new Set(`${SHOWDOWN_ARCHIVE} ${MODERN_CHARACTER_IDS}`.trim().split(/\s+/)));

export function trainerSpriteOptions(catalog: CareerCatalog | null): TrainerSpriteOption[] {
  const enriched = catalog as (CareerCatalog & { trainer_sprites?: TrainerSpriteOption[] }) | null;
  const preferred = enriched?.trainer_sprites ?? [];
  const options = new Map<string, TrainerSpriteOption>();
  for (const entry of preferred) options.set(entry.id, entry);
  for (const id of ARCHIVE_IDS) {
    if (!options.has(id)) options.set(id, { id, label: trainerSpriteLabel(id), region: "showdown" });
  }
  return Array.from(options.values());
}

export function trainerSpriteUrl(sprite: string): string {
  const id = sprite.trim().toLowerCase() || DEFAULT_TRAINER_SPRITE;
  return `${TRAINER_SPRITE_BASE}/${encodeURIComponent(id)}.png`;
}

export function trainerSpriteForRun(run: CareerRun): string {
  const rawTimeline = (run as unknown as { timeline?: unknown }).timeline;
  if (!Array.isArray(rawTimeline)) return DEFAULT_TRAINER_SPRITE;
  for (let index = rawTimeline.length - 1; index >= 0; index -= 1) {
    const entry = rawTimeline[index];
    if (!entry || typeof entry !== "object") continue;
    const event = entry as { type?: unknown; trainer_sprite?: unknown };
    if (event.type !== "trainer.appearance_selected") continue;
    if (typeof event.trainer_sprite !== "string") continue;
    const sprite = event.trainer_sprite.trim();
    if (sprite) return sprite;
  }
  return DEFAULT_TRAINER_SPRITE;
}

export function trainerSpriteStorageEntry(run: CareerRun): TrainerSpriteStorageEntry | null {
  const rawBuild = (run as unknown as { build?: { name?: unknown } }).build;
  if (typeof rawBuild?.name !== "string") return null;
  const name = rawBuild.name.trim();
  if (!name) return null;
  return {
    key: `career-trainer-sprite:${name.toLocaleLowerCase()}`,
    sprite: trainerSpriteForRun(run),
  };
}

function trainerSpriteLabel(id: string): string {
  return id
    .replace(/-(gen\d(?:rb|rs|dp|pt|bw2|bw)?|masters\d*|dueldisk|league|tundra|festival|champion|main|title)$/i, " · $1")
    .split(/[-_]/)
    .map((part) => part ? `${part[0].toUpperCase()}${part.slice(1)}` : part)
    .join(" ");
}
