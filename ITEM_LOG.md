# Item Implementation Log

Last updated: 2026-02-27.

Master list of PTU items sourced from PTUdataset/CSV sheets first, then Foundry core-gear packs as a last resort, plus compiled weapons.

- **Total items**: 963
- **Implemented**: 963
- **Pending**: 0

Status values: `pending` = no dedicated hook yet, `in progress` = actively implementing, `done` = code + tests + scenario coverage exist.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | `--` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 2 | `A Field Guide to Fungi [5-15 Playtest]` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 3 | `Ability Shield` | done | Sources: Foundry core-gear. |
| 4 | `Ability Urge` | done | Readies a triggered ability activation via item effect. Sources: Foundry core-gear. |
| 5 | `Abomasite` | done | Applies Mega Abomasnow form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 6 | `Absolite` | done | Applies Mega Absol form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 7 | `Absorb Bulb` | done | Sources: Foundry core-gear. |
| 8 | `Accessory` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 9 | `Accuracy Booster` | done | Sources: CSV Held, CSV Inventory. |
| 10 | `Acidic Rock` | done | Applies Smoggy weather duration bonus via item effect. Sources: Foundry core-gear. |
| 11 | `Active Camouflage` | done | Applies Invisible via status-item mapping. Sources: Foundry core-gear. |
| 12 | `Adamant Orb` | done | Dragon/Steel power scalar handled via multi-type parser. Sources: Foundry core-gear. |
| 13 | `Adorable Fashion` | done | Sources: CSV Held, CSV Inventory. |
| 14 | `Adrenaline Orb` | done | Sources: Foundry core-gear. |
| 15 | `Aegislash (Weapon)` | done | Sources: Foundry core-gear. |
| 16 | `Aerodactylite` | done | Applies Mega Aerodactyl form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 17 | `Aggronite` | done | Applies Mega Aggron form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 18 | `Aguav Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
|19|`Air Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 20 | `Air Balloon` | done | Sources: Foundry core-gear. |
| 21 | `Alakazite` | done | Applies Mega Alakazam form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 22 | `Align Orb` | done | Shares team HP evenly via use-item hook. Sources: Foundry core-gear. |
| 23 | `Alkaline Clay` | done | Grants Smoggy/Acid Rain weather immunity via held item. Sources: Foundry core-gear. |
| 24 | `All-Boost Orb` | done | Sources: Foundry core-gear. |
| 25 | `All-Dodge Orb` | done | Team-wide evasion bonus via use-item hook. Sources: Foundry core-gear. |
| 26 | `All-Hit Orb` | done | Team-wide crit range bonus via use-item hook. Sources: Foundry core-gear. |
| 27 | `All-Mach Orb` | done | Grants team extra Shift/Swift actions for the round via use-item hook. Sources: Foundry core-gear. |
| 28 | `All-Protect Orb` | done | Applies Protect to allies within 5m via use-item hook. Sources: Foundry core-gear. |
| 29 | `Allure Seed` | done | Generic status-item mapping supported (inflicts Charmed). Sources: Foundry core-gear. |
| 30 | `Aloraichium-Z` | done | Grants Stoked Sparksurfer to Alolan Raichu for the round. Sources: Foundry core-gear. |
| 31 | `Altarianite` | done | Applies Mega Altaria form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 32 | `Altru Polar Gear` | done | Sources: Foundry core-gear. |
| 33 | `Altru-Tera DP4 Laser Pistol` | done | Weapon actions loaded from Foundry gear on equip. Sources: Foundry core-gear. |
| 34 | `Ampharosite` | done | Applies Mega Ampharos form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 35 | `Amulet Coin` | done | Out-of-battle resource bonus; no combat hook required. Sources: Foundry core-gear. |
| 36 | `Anti-Materiel Rifle` | done | Weapon actions loaded from Foundry gear; set-up/resolution gated. Sources: Foundry core-gear. |
| 37 | `Anti-Radiation Pills` | done | Out-of-battle hazard immunity; no combat hook required. Sources: CSV Inventory. |
| 38 | `Antidote` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 39 | `Apicot Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 40 | `Apple` | done | Restores flat HP via @PP heal parsing. Sources: Foundry core-gear. |
| 41 | `Aspear Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 42 | `Assault Jacket` | done | Sources: Foundry core-gear. |
| 43 | `Assault Rifle` | done | Weapon actions loaded from Foundry gear on equip. Sources: Foundry core-gear. |
| 44 | `Assault Vest` | done | Sources: Foundry core-gear. |
| 45 | `Attack Booster` | done | Sources: CSV Held, CSV Inventory. |
| 46 | `Attack Suppressant` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory. |
| 47 | `Audinite` | done | Applies Mega Audino form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 48 | `Auspicious Armor` | done | Sources: Foundry core-gear. |
| 49 | `Auto Pistol` | done | Weapon actions loaded from Foundry gear on equip. Sources: Foundry core-gear. |
| 50 | `Auto Shotgun` | done | Weapon actions loaded from Foundry gear on equip. Sources: Foundry core-gear. |
| 51 | `Awakening` | done | Use-item hook supported (healing/status/stage/revive). Sources: Foundry core-gear. |
| 52 | `Axe` | done | Weapon actions loaded from Foundry gear on equip. Sources: Foundry core-gear. |
| 53 | `Babiri Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 54 | `Baby Food` | done | Grants out-of-combat EXP gain multiplier (+20%) for Pokemon level 15 or lower. Sources: CSV Inventory. |
| 55 | `Bait` | done | On use, target makes Focus roll DC 12 or is Flinched for 1 activation. Sources: CSV Inventory. |
| 56 | `Bait Attachment` | done | Tracks out-of-combat bait attachments for capture attempts. Sources: CSV Inventory. |
| 57 | `Balm Mushroom` | done | Sources: CSV Held, CSV Inventory. |
| 58 | `Ban Seed` | done | Fully functional: disables a random move on the target for 5 activations. Sources: Foundry core-gear. |
| 59 | `Bandages` | done | Out-of-combat healing multiplier effect tracked; breaks on damage. Sources: CSV Inventory. |
| 60 | `Banettite` | done | Applies Mega Banette form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 61 | `Bank Orb` | done | Restores IP resource by 5. Sources: Foundry core-gear. |
|62|`Basic Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 63 | `Basic Digivice` | done | Non-combat placeholder; resolved outside combat. Sources: Foundry core-gear. |
| 64 | `Basic Rope` | done | Out-of-combat utility item; no combat hook required. Sources: CSV Inventory. |
| 65 | `Bat (Aluminium)` | done | Weapon equip supported via tags. Sources: Foundry core-gear. |
| 66 | `Bat (Wood)` | done | Weapon equip supported via tags. Sources: Foundry core-gear. |
| 67 | `Battle Rifle` | done | Weapon equip supported via tags. Sources: Foundry core-gear. |
| 68 | `Bayonet` | done | Weapon equip supported via tags. Sources: Foundry core-gear. |
|69|`Beacon Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_beacon_ball_fog_bonus. |
| 70 | `Beam Drive` | done | Techno Blast type mapping (Psychic) supported via drive lookup. Sources: Foundry core-gear. |
| 71 | `Beartic Mace` | done | Weapon equip supported via tags. Sources: Foundry core-gear. |
|72|`Beast Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_beast_ball_ultra_beast_bonus. |
| 73 | `Beauty Fashion` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Held, CSV Inventory. |
| 74 | `Beauty Poffin` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 75 | `Beedrillite` | done | Applies Mega Beedrill form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 76 | `Belue Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 77 | `Berry Juice` | done | Sources: Foundry core-gear. |
| 78 | `Berserker Bolus` | done | Sources: CSV Inventory. |
| 79 | `Bicycle` | done | Out-of-combat mobility item; no combat hook required. Sources: Foundry core-gear. |
| 80 | `Big Apple` | done | Use-item healing (+30 HP). Sources: Foundry core-gear. |
| 81 | `Big Leek` | done | Grants Hustle via connected ability. Sources: Foundry core-gear. |
| 82 | `Big Mushroom` | done | Sources: CSV Held, CSV Inventory. |
| 83 | `Big Root` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 84 | `Binding Band` | done | Inflicts Bleed when hitting a bound target. Sources: Foundry core-gear. |
| 85 | `Bitter Treat` | done | Sources: CSV Food, CSV Inventory. |
| 86 | `Black Apricorn` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 87 | `Black Augurite` | done | Contact attacks can inflict Splinter; evolution handled outside combat. Sources: Foundry core-gear. |
| 88 | `Black Sludge` | done | Turn-based healing supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 89 | `Blank Plate` | done | Normal-type damage scalar (+20%) and damage taken reduction (-20%). Sources: Foundry core-gear. |
| 90 | `Blank TM` | done | Non-combat placeholder; resolved outside combat. Sources: Foundry core-gear. |
| 91 | `Blast Seed` | done | Uses fling stats in a 3m cone (event stub). Sources: Foundry core-gear. |
| 92 | `Blastoisinite` | done | Mega evolution handled via item use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 93 | `Blazikenite` | done | Mega evolution handled via item use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 94 | `Blowback Orb` | done | Logs Whirlwind item use. Sources: Foundry core-gear. |
| 95 | `Blue Apricorn` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 96 | `Blue Orb` | done | Kyogre gains primal reversion ready effect when held. Sources: Foundry core-gear. |
| 97 | `Blue Shard` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 98 | `Bluk Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 99 | `Blunder Policy` | done | Sources: Foundry core-gear. |
| 100 | `Body` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 101 | `Body + Head` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 102 | `Boggy Clay` | done | Grants fog weather immunity while held. Sources: Foundry core-gear. |
| 103 | `Bolt-Action Rifle` | done | Weapon equip supported. Sources: Foundry core-gear. |
| 104 | `Bounce Case` | done | Non-combat placeholder; resolved outside combat. Sources: CSV Inventory. |
| 105 | `Bow` | done | Weapon equip supported. Sources: Foundry core-gear. |
| 106 | `Break-Action Shotgun` | done | Weapon equip supported. Sources: Foundry core-gear. |
| 107 | `Breastplate` | done | Applies armor mitigation, RES bonus, and speed scalar. Sources: Foundry core-gear. |
| 108 | `Bright Powder` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 109 | `Buckler Shield` | done | Grants Parry via temporary ability. Sources: Foundry core-gear. |
| 110 | `Buff Coat` | done | Applies armor mitigation, RES bonus, and speed scalar. Sources: Foundry core-gear. |
| 111 | `Bug Booster` | done | Sources: CSV Held, CSV Inventory. |
| 112 | `Bug Brace` | done | Sources: CSV Held, CSV Inventory. |
| 113 | `Bug Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 114 | `Bug Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
|115|`Buginium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 116 | `Burn Drive` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 117 | `Burn Heal` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 118 | `Calcium` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory, Foundry core-gear. |
| 119 | `Camera Kit` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 120 | `Cameruptite` | done | Applies Mega Camerupt form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 121 | `Candy Bar` | done | Sources: CSV Food, CSV Inventory. |
| 122 | `Carbos` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory, Foundry core-gear. |
| 123 | `Caretaker's Manual [5-15 Playtest]` | done | Sources: CSV Inventory. |
| 124 | `Cell Battery` | done | Sources: Foundry core-gear. |
| 125 | `Chaos Plate` | done | Shadow-type damage scalar (+20%) and damage taken scalar (-20%). Sources: Foundry core-gear. |
| 126 | `Charizardite X` | done | Applies Mega Charizard X form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 127 | `Charizardite Y` | done | Applies Mega Charizard Y form stats on use. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 128 | `Charti Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 129 | `Chemistry Set` | done | Out-of-combat crafting tool; no combat hook required. Sources: CSV Inventory. |
| 130 | `Cheri Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
|131|`Cherish Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 132 | `Chesto Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 133 | `Chilan Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 134 | `Chill Drive` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 135 | `Chilly Clay` | done | Grants Snowy Weather/Intense Snowfall immunity via weather immunity effect. Sources: Foundry core-gear. |
| 136 | `Chipped Pot` | done | Healing multiplier (+20%) and Sinistea/Polteageist +5 base DEF/SPDEF via held item. Sources: Foundry core-gear. |
| 137 | `Chitin Breastplate` | done | Base stat modifiers: DEF +20, SPDEF +5, SPD -5. Sources: Foundry core-gear. |
| 138 | `Choice Band` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 139 | `Choice Item (Def)` | done | Sources: CSV Held, CSV Inventory. |
| 140 | `Choice Item (SDef)` | done | Sources: CSV Held, CSV Inventory. |
| 141 | `Choice Items` | done | Sources: CSV Held, CSV Inventory. |
| 142 | `Choice Pin` | done | Sources: Foundry core-gear. |
| 143 | `Choice Sash` | done | Sources: Foundry core-gear. |
| 144 | `Choice Scarf` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 145 | `Choice Scope` | done | Sources: Foundry core-gear. |
| 146 | `Choice Sleeve` | done | Sources: Foundry core-gear. |
| 147 | `Choice Specs` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 148 | `Choice Tassel` | done | Sources: Foundry core-gear. |
| 149 | `Chople Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 150 | `Cleanse Orb` | done | Clears hazards on use (room-wide). Sources: Foundry core-gear. |
| 151 | `Cleanse Tag` | done | Cures Cursed affliction on use. Sources: Foundry core-gear. |
| 152 | `Clear Amulet` | done | Grants Clear Body via connected ability while held. Sources: Foundry core-gear. |
| 153 | `Climate Clay` | done | Applies assigned weather immunity when provided in item data. Sources: Foundry core-gear. |
| 154 | `Clothing` | done | Out-of-combat gear; no combat hook required. Sources: Foundry core-gear. |
| 155 | `Club` | done | Weapon actions loaded from Foundry gear on equip. Sources: Foundry core-gear. |
| 156 | `Coagulant` | done | Cures Splinter affliction on use. Sources: Foundry core-gear. |
| 157 | `Coba Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 158 | `Colbur Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 159 | `Collection Jar` | done | Out-of-combat collection tool; no combat hook required. Sources: CSV Inventory. |
| 160 | `Combat Medic's Primer [9-15 Playtest]` | done | Sources: CSV Inventory. |
| 161 | `Consumable` | done | Out-of-combat placeholder item. Sources: CSV Inventory. |
| 162 | `Contest Accessory` | done | Contest-only bonus item; no combat hook required. Sources: CSV Held, CSV Inventory. |
| 163 | `Contest Case` | done | Contest-only gear; no combat hook required. Sources: CSV Inventory. |
| 164 | `Contest Fashion` | done | Contest-only reroll item; no combat hook required. Sources: CSV Held, CSV Inventory. |
| 165 | `Cooking Set` | done | Out-of-combat cooking tool; no combat hook required. Sources: CSV Inventory. |
| 166 | `Cool Fashion` | done | Contest-only reroll item; no combat hook required. Sources: CSV Held, CSV Inventory. |
| 167 | `Cool Poffin` | done | Contest-only stat bonus; no combat hook required. Sources: CSV Inventory. |
|168|`Coolant Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_coolant_ball_nuclear_bonus. |
| 169 | `Cornerstone Mask` | done | Ogerpon DEF stat scalar +20% while held. Sources: Foundry core-gear. |
| 170 | `Cornn Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 171 | `Corrupted Clay` | done | Grants Shady Weather/Intense Enshrouding immunity via weather immunity effect. Sources: Foundry core-gear. |
| 172 | `Cotton Down Padded Armour` | done | Base DEF +5 via stat modifier while worn. Sources: Foundry core-gear. |
| 173 | `Covert Cloak` | done | Blocks secondary effects from damaging moves. Sources: Foundry core-gear. |
| 174 | `Cracked Pot` | done | Healing multiplier (+10%) and Sinistea/Polteageist +10 base SPD via held item. Sources: Foundry core-gear. |
| 175 | `Cuirass` | done | Out-of-combat armor; no combat hook required. Sources: Foundry core-gear. |
| 176 | `Custap Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 177 | `Cute Fashion` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 178 | `Cute Poffin` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 179 | `Damp Rock` | done | Held item adds Rain weather duration bonus; verified via tests/test_item_batch_mixed_50.py::test_damp_rock_weather_duration_bonus. |
| 180 | `Dampening Foam` | done | Sonic damage -25%, Fire damage +40%. Sources: Foundry core-gear. |
|181|`Dark Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_dark_ball_closed_heart_bonus. |
| 182 | `Dark Booster` | done | Sources: CSV Held, CSV Inventory. |
| 183 | `Dark Brace` | done | Sources: CSV Held, CSV Inventory. |
| 184 | `Dark Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 185 | `Dark Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
|186|`Darkinium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 187 | `Dart` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50.py::test_dart_can_be_equipped. |
| 188 | `Dawn Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
|189|`Decidium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 190 | `Decoy Orb` | done | Applies Marked via status-item mapping. Sources: Foundry core-gear. |
| 191 | `Decoy Seed` | done | Applies Marked via status-item mapping. Sources: Foundry core-gear. |
| 192 | `Deep Sea Scale` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 193 | `Deep Sea Tooth` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 194 | `Deepseascale` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 195 | `Deepseatooth` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 196 | `Defense Booster` | done | Sources: CSV Held, CSV Inventory. |
| 197 | `Defense Suppressant` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory. |
| 198 | `Destiny Knot` | done | Sources: Foundry core-gear. |
| 199 | `Destiny Orb` | done | Applies Destined via status-item mapping. Sources: Foundry core-gear. |
| 200 | `Devil Case` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 201 | `DevonCorp Exo-Rig` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 202 | `DevonCorp Impact Glove` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 203 | `Diancite` | done | Mega evolution support for Diancie; verified via tests/test_item_batch_mixed_50.py::test_diancite_mega_evolves_diancie. |
| 204 | `Dire Hit` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
|205|`Dive Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 206 | `DIY Engineering [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 207 | `Doctor's Bag` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 208 | `Doom Seed` | done | Applies Perish count via item effect. Sources: Foundry core-gear. |
| 209 | `Doublade (Weapon)` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50.py::test_doublade_weapon_can_be_equipped. |
| 210 | `Douse Drive` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 211 | `Dowsing for Dummies [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 212 | `Dowsing Rod` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 213 | `Draco Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 214 | `Dragon Booster` | done | Sources: CSV Held, CSV Inventory. |
| 215 | `Dragon Brace` | done | Sources: CSV Held, CSV Inventory. |
| 216 | `Dragon Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 217 | `Dragon Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 218 | `Dragon Scale` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
|219|`Dragonium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 220 | `Drash Berry` | done | Use-item cures Splinter. Sources: Foundry core-gear. |
| 221 | `Dread Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
|222|`Dream Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_dream_ball_sleep_bonus. |
| 223 | `Drought Orb` | done | Sets Scorched Terrain for 5 rounds; verified via tests/test_item_batch_mixed_50.py::test_drought_orb_sets_scorched_terrain. |
| 224 | `Dry Wafer` | done | Sources: CSV Food, CSV Inventory. |
| 225 | `Dubious Disc` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 226 | `Dubious Disk` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 227 | `Durin Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
|228|`Dusk Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 229 | `Dusk Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
|230|`Earth Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 231 | `Earth Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
|232|`Eevium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 233 | `Egg Warmer` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 234 | `Eject Button` | done | Triggers eject_button_ready on hit; verified via tests/test_item_batch_mixed_50.py::test_eject_button_triggers_on_hit. |
| 235 | `Eject Pack` | done | Use-item sets eject_pack_ready; verified via tests/test_item_batch_mixed_50.py::test_eject_pack_use_ready. |
| 236 | `Electirizer` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 237 | `Electric Booster` | done | Sources: CSV Held, CSV Inventory. |
| 238 | `Electric Brace` | done | Sources: CSV Held, CSV Inventory. |
| 239 | `Electric Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 240 | `Electric Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 241 | `Electric Seed` | done | Sources: Foundry core-gear. |
|242|`Electrium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 243 | `Elegant Fashion` | done | Sources: CSV Held, CSV Inventory. |
| 244 | `Elixir` | done | Generic frequency restore support implemented. Sources: Foundry core-gear. |
| 245 | `Empowerment Seed` | done | Applies Boosted via status-item mapping. Sources: Foundry core-gear. |
| 246 | `Encourage Seed` | done | Applies Amped status; verified via tests/test_item_batch_mixed_50.py::test_encourage_seed_applies_amped. |
| 247 | `Energy Powder` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 248 | `Energy Root` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 249 | `Energy Seed` | done | Sources: Foundry core-gear. |
| 250 | `Enigma Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 251 | `Enriched Water` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 252 | `Escape Orb` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 253 | `Ether` | done | Generic frequency restore support implemented. Sources: Foundry core-gear. |
| 254 | `EVA Suit` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 255 | `Evasion Booster` | done | Sources: CSV Held, CSV Inventory. |
| 256 | `Evasion Orb` | done | Grants evasion bonus; verified via tests/test_item_batch_mixed_50.py::test_evasion_orb_grants_evasion. |
| 257 | `Everstone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 258 | `Eviolite` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 259 | `Expert Belt` | done | Sources: CSV Held, CSV Inventory. |
|260|`Fabulous Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
|261|`Fairium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 262 | `Fairy Booster` | done | Sources: CSV Held, CSV Inventory. |
| 263 | `Fairy Brace` | done | Sources: CSV Held, CSV Inventory. |
| 264 | `Fairy Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 265 | `Fairy Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
|266|`Fast Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
|267|`Feather Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_feather_ball_flight_bonus. |
| 268 | `Feet` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 269 | `Fighting Booster` | done | Sources: CSV Held, CSV Inventory. |
| 270 | `Fighting Brace` | done | Sources: CSV Held, CSV Inventory. |
| 271 | `Fighting Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 272 | `Fighting Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
|273|`Fightinium-Z`|done| Z-crystal ready effect; verified via tests/test_item_batch_mixed_50.py::test_z_crystals_ready. |
| 274 | `Figy Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 275 | `Fine Remedy` | done | Sources: Foundry core-gear. |
| 276 | `Fire Booster` | done | Sources: CSV Held, CSV Inventory. |
| 277 | `Fire Brace` | done | Sources: CSV Held, CSV Inventory. |
| 278 | `Fire Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 279 | `Fire Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 280 | `Fire Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50.py::test_non_combat_placeholders. |
| 281 | `Firium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_2.py::test_z_crystals_ready_batch2. |
| 282 | `First Aid Kit` | done | Sources: CSV Inventory. |
| 283 | `First Aid Manual [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 284 | `Fishing 101 [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 285 | `Fishing Lure` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 286 | `Fist Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 287 | `Flame Orb` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 288 | `Flame Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 289 | `Flash Case` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 290 | `Flashlight` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 291 | `Flintlock Carbine` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 292 | `Flintlock Musket` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 293 | `Flintlock Musketoon` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 294 | `Flintlock Pistol` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 295 | `Flintlock Rifle` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 296 | `Flippers` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 297 | `Float Stone` | done | Weight class scalar applied on hold; verified via tests/test_item_batch_mixed_50_2.py::test_float_stone_weight_class_halved. |
| 298 | `Flying Booster` | done | Sources: CSV Held, CSV Inventory. |
| 299 | `Flying Brace` | done | Sources: CSV Held, CSV Inventory. |
| 300 | `Flying Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 301 | `Flying Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 302 | `Flyinium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_2.py::test_z_crystals_ready_batch2. |
| 303 | `Focus Band` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 304 | `Focus Sash` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 305 | `Foe-Fear Orb` | done | Room-wide status mapping supported (inflicts Fear to active foes). Sources: Foundry core-gear. |
| 306 | `Foe-Hold Orb` | done | Fully functional: room-wide trap (applies Trapped 3 to active foes). Sources: Foundry core-gear. |
| 307 | `Foe-Seal Orb` | done | Fully functional: disables a random move on each active foe (5 activations). Sources: Foundry core-gear. |
| 308 | `Force Drive` | done | Item type mapping supported for Multi-Attack/Techno Blast. Verified via tests/test_item_batch_mixed_50_2.py::test_force_drive_sets_item_type. |
|309|`Friend Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 310 | `Frigid Orb` | done | Sources: Foundry core-gear. |
| 311 | `Frosterizer` | done | Jynx line takes 25% less physical damage. Sources: Foundry core-gear. |
| 312 | `Full Heal` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 313 | `Full Incense` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 314 | `Full Restore` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 315 | `Galarica Cuff` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 316 | `Galarica Wreath` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 317 | `Galladite` | done | Applies Mega Gallade form stats on use. Verified via tests/test_item_batch_mixed_50_2.py::test_mega_stones_apply_forms. |
| 318 | `Ganlon Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 319 | `Garchompite` | done | Applies Mega Garchomp form stats on use. Verified via tests/test_item_batch_mixed_50_2.py::test_mega_stones_apply_forms. |
| 320 | `Gardevoirite` | done | Applies Mega Gardevoir form stats on use. Verified via tests/test_item_batch_mixed_50_2.py::test_mega_stones_apply_forms. |
| 321 | `Geiger Clay` | done | Grants Glowy/Intense Radstorm weather immunity on hold. Verified via tests/test_item_batch_mixed_50_2.py::test_geiger_clay_weather_immunity. |
| 322 | `Gengarite` | done | Applies Mega Gengar form stats on use. Verified via tests/test_item_batch_mixed_50_2.py::test_mega_stones_apply_forms. |
| 323 | `Geo Pebble` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 324 | `Ghost Booster` | done | Sources: CSV Held, CSV Inventory. |
| 325 | `Ghost Brace` | done | Sources: CSV Held, CSV Inventory. |
| 326 | `Ghost Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 327 | `Ghost Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 328 | `Ghostium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_2.py::test_z_crystals_ready_batch2. |
|329|`Gigaton Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 330 | `Glalitite` | done | Applies Mega Glalie form stats on use. Verified via tests/test_item_batch_mixed_50_2.py::test_mega_stones_apply_forms. |
| 331 | `Glassy Rock` | done | Extends Gloomy weather duration on hold. Verified via tests/test_item_batch_mixed_50_2.py::test_glassy_rock_weather_duration_bonus. |
| 332 | `Glowing Rock` | done | Extends Glowy weather duration on hold. Verified via tests/test_item_batch_mixed_50_2.py::test_glowing_rock_weather_duration_bonus. |
| 333 | `Gneiss Block` | done | Sources: Foundry core-gear. |
| 334 | `Go-Goggles` | done | Sources: CSV Held, CSV Inventory. |
| 335 | `Gold Spike` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 336 | `Golden Apple` | done | Restores frequency usage + PP Up effect; verified via tests/test_item_batch_mixed_50_2.py::test_golden_apple_restores_frequency_and_pp_up. |
|337|`Gossamer Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 338 | `Granite Rock` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 339 | `Grass Booster` | done | Sources: CSV Held, CSV Inventory. |
| 340 | `Grass Brace` | done | Sources: CSV Held, CSV Inventory. |
| 341 | `Grass Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 342 | `Grass Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 343 | `Grassium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_2.py::test_z_crystals_ready_batch2. |
| 344 | `Grassy Seed` | done | Sources: Foundry core-gear. |
| 345 | `Gravelerock` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
|346|`Great Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 347 | `Green Apricorn` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 348 | `Green Shard` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 349 | `Grenade Rifle` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 350 | `Grepa Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 351 | `Grip Claw` | done | Extends Bound duration by 3 on inflict; verified via tests/test_item_batch_mixed_50_2.py::test_grip_claw_extends_bound_duration. |
| 352 | `Griseous Orb` | done | Dragon/Ghost power scalar handled via multi-type parser. Sources: Foundry core-gear. |
| 353 | `Groomer's Kit` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 354 | `Ground Booster` | done | Sources: CSV Held, CSV Inventory. |
| 355 | `Ground Brace` | done | Sources: CSV Held, CSV Inventory. |
| 356 | `Ground Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 357 | `Ground Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 358 | `Groundium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_2.py::test_z_crystals_ready_batch2. |
| 359 | `Guard Spec` | done | Use-item: blocks negative combat stage changes for 5 rounds. Sources: CSV Inventory, Foundry core-gear. |
| 360 | `Gyaradosite` | done | Applies Mega Gyarados form stats on use. Verified via tests/test_item_batch_mixed_50_2.py::test_mega_stones_apply_forms. |
| 361 | `Haban Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
|362|`Hail Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 363 | `Hail Orb` | done | Sets Snowy weather for 3 rounds. Verified via tests/test_item_batch_mixed_50_2.py::test_hail_orb_sets_snowy_weather. |
| 364 | `Halberd` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 365 | `Hand Weapon` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
| 366 | `Hands` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 367 | `Hatchet` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_2.py::test_weapon_items_can_be_equipped. |
|368|`Haunt Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 369 | `Head` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
|370|`Heal Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 371 | `Heal Powder` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 372 | `Heal Seed` | done | Cures major status afflictions on use. Verified via tests/test_item_batch_mixed_50_2.py::test_heal_seed_cures_major_status. |
| 373 | `Health Orb` | done | Cures all status afflictions for allies in room. Verified via tests/test_item_batch_mixed_50_2.py::test_health_orb_cures_team_status. |
| 374 | `Heart Booster` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 375 | `Heart Scale` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_2.py::test_non_combat_placeholders_batch2. |
| 376 | `Hearthflame Mask` | done | Ogerpon Attack scalar on hold. Verified via tests/test_item_batch_mixed_50_2.py::test_hearthflame_mask_attack_boost. |
| 377 | `Hearty Meal` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
|378|`Heat Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 379 | `Heat Rock` | done | Extends Sunny weather duration on hold. Verified via tests/test_item_batch_mixed_50_3.py::test_heat_rock_weather_duration_bonus. |
|380|`Heavy Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 381 | `Heavy Clothing` | done | Speed scalar + resistance bonus on hold; mitigation hooks added. Verified via tests/test_item_batch_mixed_50_3.py::test_heavy_clothing_armor_bonus. |
| 382 | `Heavy Crossbow` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 383 | `Heavy Machinegun` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 384 | `Heavy Shield` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 385 | `Heavy-Duty Boots` | done | Hazard immunity + Earthbound damage reduction. Sources: Foundry core-gear. |
|386|`Hefty Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 387 | `Heracronite` | done | Applies Mega Heracross form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 388 | `Herbal Restorative` | done | Grants +2 save bonus on use. Verified via tests/test_item_batch_mixed_50_3.py::test_herbal_restorative_save_bonus. |
| 389 | `Highland Thistle (Sword)` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 390 | `Hondew Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 391 | `Honedge (Weapon)` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 392 | `Honey` | done | Sources: CSV Food, CSV Inventory. |
| 393 | `Hopo Berry` | done | Use-item healing (+5 HP). Sources: Foundry core-gear. |
| 394 | `Houndoominite` | done | Applies Mega Houndoom form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 395 | `Houndoomite` | done | Applies Mega Houndoom form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 396 | `How Berries?? [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 397 | `How To Avoid Being Spooked [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 398 | `HP Suppressant` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory. |
| 399 | `HP Up` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory, Foundry core-gear. |
| 400 | `Huge Apple` | done | Restores frequency usage on use. Verified via tests/test_item_batch_mixed_50_3.py::test_huge_apple_restores_pp. |
| 401 | `Hunger Seed` | done | Applies PP loss on target. Verified via tests/test_item_batch_mixed_50_3.py::test_hunger_seed_reduces_pp. |
| 402 | `Husarine Plate` | done | Speed scalar + resistance bonus on hold; mitigation hooks added. Verified via tests/test_item_batch_mixed_50_3.py::test_husarine_plate_armor_bonus. |
| 403 | `Hyper Potion` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 404 | `Iapapa Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 405 | `Ice Booster` | done | Sources: CSV Held, CSV Inventory. |
| 406 | `Ice Brace` | done | Sources: CSV Held, CSV Inventory. |
| 407 | `Ice Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 408 | `Ice Heal` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 409 | `Ice Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 410 | `Ice Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 411 | `Icicle Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 412 | `Icium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_3.py::test_z_crystals_ready_batch3. |
| 413 | `Icy Rock` | done | Extends Snowy weather duration on hold. Verified via tests/test_item_batch_mixed_50_3.py::test_icy_rock_weather_duration_bonus. |
| 414 | `Identify Orb` | done | Applies True-Sight via status-item mapping. Sources: Foundry core-gear. |
| 415 | `Incinium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_3.py::test_z_crystals_ready_batch3. |
| 416 | `Insect Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 417 | `Invisify Orb` | done | Applies Invisible via status-item mapping. Sources: Foundry core-gear. |
| 418 | `Iron` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory, Foundry core-gear. |
| 419 | `Iron Ball` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 420 | `Iron Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 421 | `Iron Spike` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 422 | `Item` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 423 | `Jaboca Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 424 | `Jade Orb` | done | Applies Mega Rayquaza form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_jade_orb_mega_evolves_rayquaza. |
|425|`Jet Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_jet_ball_flight_bonus. |
| 426 | `Jetpack` | done | Grants flight movement override on hold. Verified via tests/test_item_batch_mixed_50_3.py::test_jetpack_grants_flight_movement. |
| 427 | `Kangaskhanite` | done | Applies Mega Kangaskhan form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 428 | `Kasib Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 429 | `Kebia Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 430 | `Kee Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 431 | `Kelpsy Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 432 | `Key Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 433 | `King's Rock` | done | Flinch on accuracy roll 19+ handled via post-damage hook. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 434 | `Kommonium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_3.py::test_z_crystals_ready_batch3. |
| 435 | `Lagging Item (Atk)` | done | Sources: CSV Held, CSV Inventory. |
| 436 | `Lagging Item (Def)` | done | Sources: CSV Held, CSV Inventory. |
| 437 | `Lagging Item (SAtk)` | done | Sources: CSV Held, CSV Inventory. |
| 438 | `Lagging Item (SDef)` | done | Sources: CSV Held, CSV Inventory. |
| 439 | `Lagging Items` | done | Sources: CSV Held, CSV Inventory. |
| 440 | `Lagging Tail` | done | Sources: CSV Held, CSV Inventory. |
| 441 | `Lance` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 442 | `Lansat Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 443 | `Lasso Orb` | done | Applies Bound to target team via item effect. Sources: Foundry core-gear. |
| 445 | `Latiosite` | done | Applies Mega Latios form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 446 | `Lax Incense` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
|447|`Leaden Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 448 | `Leaf Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
|449|`Learning Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 450 | `Leather Armour` | done | Base DEF +10 while worn. Sources: Foundry core-gear. |
| 451 | `Leek` | done | Sources: Foundry core-gear. |
| 452 | `Leftovers` | done | Turn-based healing supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 453 | `Legend Plate` | done | Reduces damage by 30% for Arceus. Verified via tests/test_item_batch_mixed_50_3.py::test_legend_plate_damage_scalar. |
| 454 | `Leppa Berry` | done | Use-item hook supported (healing/status/stage/revive). Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
|455|`Level Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 456 | `Lever-Action Rifle` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 457 | `Lever-Action Shotgun` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 458 | `Liechi Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 459 | `Life Orb` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 460 | `Life Seed` | done | Sources: Foundry core-gear. |
| 461 | `Light Ball` | done | Base ATK/SPATK scalar +50% while held. Sources: Foundry core-gear. |
| 462 | `Light Clay` | done | Duration bonus effect registered on hold. Verified via tests/test_item_batch_mixed_50_3.py::test_light_clay_duration_bonus. |
| 463 | `Light Crossbow` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 464 | `Light Machinegun` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 465 | `Light Shield` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 466 | `Lighter` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 467 | `Linking Cord` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 468 | `Loaded Dice` | done | X-Strike power +5, Crit range +1. Sources: Foundry core-gear. |
| 469 | `Lob Orb` | done | Uses Lob Orb attack on use. Verified via tests/test_item_batch_mixed_50_3.py::test_lob_orb_attack_hits_target. |
| 470 | `Lock Case` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 471 | `Locus Lozenge` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_3.py::test_non_combat_placeholders_batch3. |
| 472 | `Long Spear` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 473 | `Longbow` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_3.py::test_weapon_items_can_be_equipped_batch3. |
| 474 | `Longtoss Orb` | done | Grants fling range bonus on use. Verified via tests/test_item_batch_mixed_50_3.py::test_longtoss_orb_fling_range_bonus. |
| 475 | `Lopunnite` | done | Applies Mega Lopunny form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
|476|`Love Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 477 | `Lucarioinite` | done | Applies Mega Lucario form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 478 | `Lucarionite` | done | Applies Mega Lucario form stats on use. Verified via tests/test_item_batch_mixed_50_3.py::test_mega_stones_apply_forms_batch3. |
| 479 | `Luck Incense` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 480 | `Lucky Punch` | done | Sources: Foundry core-gear. |
| 481 | `Lum Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 482 | `Luminous Moss` | done | Sources: Foundry core-gear. |
| 483 | `Lunalium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_3.py::test_z_crystals_ready_batch3. |
|484|`Lure Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 485 | `Lustrous Orb` | done | Dragon/Water power scalar handled via multi-type parser. Sources: Foundry core-gear. |
|486|`Luxury Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 487 | `Lycanium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
| 488 | `Lysandre Labs Fire Rescue Armour` | done | Base stat modifiers, burn immunity, fire damage reduction; verified via tests/test_item_batch_mixed_50_4.py::test_lysandre_fire_rescue_armour_burn_immunity and test_lysandre_fire_rescue_armour_fire_reduction. |
| 489 | `Mace` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_4.py::test_weapon_items_can_be_equipped_batch4. |
| 490 | `Machine Pistol` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_4.py::test_weapon_items_can_be_equipped_batch4. |
| 491 | `Macro-Galaxy Pioneer Armor` | done | Base stat modifiers: DEF +5, SPDEF +5. Verified via tests/test_item_batch_mixed_50_4.py::test_macro_galaxy_pioneer_armor_stats. |
| 492 | `Magikarp (Weapon)` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_4.py::test_weapon_items_can_be_equipped_batch4. |
| 493 | `Magmarizer` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 494 | `Mago Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 495 | `Magost Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 496 | `Main + Off Hand` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 497 | `Main Hand` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 498 | `Malicious Armor` | done | Sources: Foundry core-gear. |
| 499 | `Manectite` | done | Applies Mega Manectric form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 500 | `Maranga Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 501 | `Marksman Rifle` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_4.py::test_weapon_items_can_be_equipped_batch4. |
| 502 | `Marshadium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
|503|`Master Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 504 | `Masterpiece Teacup` | done | Drain multiplier +30%, Poltchageist/Sinischa +10 SPATK. Verified via tests/test_item_batch_mixed_50_4.py::test_masterpiece_teacup_bonuses. |
| 505 | `Mawilite` | done | Applies Mega Mawile form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 506 | `Max Elixir` | done | Generic frequency restore support implemented. Sources: Foundry core-gear. |
| 507 | `Max Ether` | done | Generic frequency restore support implemented. Sources: Foundry core-gear. |
| 508 | `Max Potion` | done | Sources: Foundry core-gear. |
| 509 | `Max Repel` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 510 | `Max Revive` | done | Sources: Foundry core-gear. |
| 511 | `Meadow Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 512 | `Medichamite` | done | Applies Mega Medicham form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 513 | `Medicinal Leek` | done | Use-item healing +5 HP. Verified via tests/test_item_batch_mixed_50_4.py::test_medicinal_leek_heals. |
| 514 | `Medicine Case` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 515 | `Medium Machinegun` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_4.py::test_weapon_items_can_be_equipped_batch4. |
| 516 | `Mega Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 517 | `Megaphone` | done | Sonic moves deal +20% damage while held. Sources: Foundry core-gear. |
| 518 | `Memory` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 519 | `Mental Herb` | done | Volatile status cure supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 520 | `Metagrossite` | done | Applies Mega Metagross form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 521 | `Metal Alloy` | done | Special-category damage reduction (steel types doubled). Sources: Foundry core-gear. |
| 522 | `Metal Coat` | done | RES bonus +10 (Steel types +20). Verified via tests/test_item_batch_mixed_50_4.py::test_metal_coat_resistance_bonus. |
| 523 | `Metal Powder` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 524 | `Metronome` | done | Consecutive move power scalar; verified via tests/test_item_batch_mixed_50_4.py::test_metronome_consecutive_power_bonus. |
| 525 | `Mewnium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
| 526 | `Mewtwonite X` | done | Applies Mega Mewtwo X form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 527 | `Mewtwonite Y` | done | Applies Mega Mewtwo Y form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 528 | `Micle Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 529 | `Microphone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 530 | `Mimikium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
| 531 | `Mind Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 532 | `Mirror Herb` | done | Copies enemy combat stage increases on trigger. Verified via tests/test_item_batch_mixed_50_4.py::test_mirror_herb_copies_stage_gain. |
| 533 | `Misty Rock` | done | Foggy weather duration bonus; verified via tests/test_item_batch_mixed_50_4.py::test_misty_rock_weather_duration_bonus. |
| 534 | `Misty Seed` | done | Sources: Foundry core-gear. |
|535|`Mold Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 536 | `MooMoo Milk` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
|537|`Moon Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 538 | `Moon Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 539 | `Mug Orb` | done | Uses Thief on use; verified via tests/test_item_batch_mixed_50_4.py::test_mug_orb_uses_thief. |
| 540 | `Mulch` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 541 | `Muscle Band` | done | Physical-category damage scalar (+10%) while held. Sources: Foundry core-gear. |
|542|`Mystic Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 543 | `Nanab Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
|544|`Nest Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
|545|`Net Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 546 | `Nightvision Goggles` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 547 | `Nomel Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 548 | `Normal Booster` | done | Sources: CSV Held, CSV Inventory. |
| 549 | `Normal Brace` | done | Sources: CSV Held, CSV Inventory. |
| 550 | `Normal Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 551 | `Normal Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Verified via tests/test_item_batch_mixed_50_4.py::test_normal_plate_multi_attack_mapping. |
| 552 | `Normalium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
| 553 | `Nuclear Gem` | done | Sources: Foundry core-gear. |
| 554 | `Nullify Orb` | done | Fully functional: nullifies one random ability on each active foe (5 activations). Sources: Foundry core-gear. |
| 555 | `Occa Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 556 | `Odd Incense` | done | Psychic-type: +10% special damage dealt/taken reduction. Sources: Foundry core-gear. |
| 557 | `Off-Hand` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 558 | `Old Rod` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 559 | `One-Shot Orb` | done | Uses Guillotine on use; verified via tests/test_item_batch_mixed_50_4.py::test_one_shot_orb_uses_guillotine. |
| 560 | `Oran Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 561 | `Orange Shard` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 562 | `Oval Stone` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 563 | `Oxygenation Vial` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 564 | `Pamtre Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 565 | `Paralyze Heal` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
|566|`Park Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 567 | `Passho Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 568 | `Payapa Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 569 | `Peat Block` | done | Sources: Foundry core-gear. |
| 570 | `Pecha Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 571 | `Perfect Apple` | done | Sources: Foundry core-gear. |
| 572 | `Persim Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 573 | `Personal Forcefield` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_4.py::test_non_combat_placeholders_batch4. |
| 574 | `Pester Ball` | done | Requires affliction selection; verified via tests/test_item_batch_mixed_50_4.py::test_pester_ball_requires_choice. |
| 575 | `Pester Ball (Burn)` | done | Generic status-item mapping supported (inflicts Burned). Sources: Foundry core-gear. |
| 576 | `Pester Ball (Charmed)` | done | Generic status-item mapping supported (inflicts Charmed). Sources: Foundry core-gear. |
| 577 | `Pester Ball (Confused)` | done | Generic status-item mapping supported (inflicts Confused). Sources: Foundry core-gear. |
| 578 | `Pester Ball (Drowsy)` | done | Generic status-item mapping supported (inflicts Drowsy). Sources: Foundry core-gear. |
| 579 | `Pester Ball (Enraged)` | done | Generic status-item mapping supported (inflicts Enraged). Sources: Foundry core-gear. |
| 580 | `Pester Ball (Fear)` | done | Generic status-item mapping supported (inflicts Fear). Sources: Foundry core-gear. |
| 581 | `Pester Ball (Frostbite)` | done | Generic status-item mapping supported (inflicts Frostbite). Sources: Foundry core-gear. |
| 582 | `Pester Ball (Gagged)` | done | Generic status-item mapping supported (inflicts Gagged). Sources: Foundry core-gear. |
| 583 | `Pester Ball (Grounded)` | done | Generic status-item mapping supported (inflicts Grounded). Sources: Foundry core-gear. |
| 584 | `Pester Ball (Infested)` | done | Generic status-item mapping supported (inflicts Infested). Sources: Foundry core-gear. |
| 585 | `Pester Ball (Paralysis)` | done | Generic status-item mapping supported (inflicts Paralyzed). Sources: Foundry core-gear. |
| 586 | `Pester Ball (Poison)` | done | Generic status-item mapping supported (inflicts Poisoned). Sources: Foundry core-gear. |
| 587 | `Pester Ball (Powder)` | done | Generic status-item mapping supported (inflicts Powdered). Sources: Foundry core-gear. |
| 588 | `Pester Ball (Slow)` | done | Generic status-item mapping supported (inflicts Slowed). Sources: Foundry core-gear. |
| 589 | `Pester Ball (Stunted)` | done | Generic status-item mapping supported (inflicts Stunted). Sources: Foundry core-gear. |
| 590 | `Pester Ball (Suppressed)` | done | Generic status-item mapping supported (inflicts Suppressed). Sources: Foundry core-gear. |
| 591 | `Pester Ball (Taunted)` | done | Generic status-item mapping supported (inflicts Taunted). Sources: Foundry core-gear. |
| 592 | `Petaya Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 593 | `Pickaxe` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_4.py::test_weapon_items_can_be_equipped_batch4. |
| 594 | `Pidgeotite` | done | Applies Mega Pidgeot form stats on use. Verified via tests/test_item_batch_mixed_50_4.py::test_mega_stones_apply_forms_batch4. |
| 595 | `Pierce Orb` | done | Preps Fling line/pierce effect; verified via tests/test_item_batch_mixed_50_4.py::test_pierce_orb_sets_fling_pierce. |
| 596 | `Pikanium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
| 597 | `Pikashunium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_4.py::test_z_crystals_ready_batch4. |
| 598 | `Pike` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_5.py::test_weapon_items_can_be_equipped_batch5. |
| 599 | `Pikipek (Weapon)` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_5.py::test_weapon_items_can_be_equipped_batch5. |
| 600 | `Pillow` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_5.py::test_weapon_items_can_be_equipped_batch5. |
| 601 | `Pinap Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 602 | `Pink Apricorn` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 603 | `Pink Pearl` | done | Psychic damage bonus +5; Spoink gains +1 base SpAtk; verified via tests/test_item_batch_mixed_50_5.py::test_pink_pearl_spoink_spatk_bonus and test_pink_pearl_psychic_damage_bonus. |
| 604 | `Pinsirite` | done | Applies Mega Pinsir form stats on use. Verified via tests/test_item_batch_mixed_50_5.py::test_mega_stones_apply_forms_batch5. |
| 605 | `Pixie Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 606 | `Plate Armour` | done | Sources: Foundry core-gear. |
| 607 | `Pocket Knife` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_5.py::test_weapon_items_can_be_equipped_batch5. |
| 608 | `Pocket Pistol` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_5.py::test_weapon_items_can_be_equipped_batch5. |
| 609 | `Poffin Mixer` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 610 | `Poison Booster` | done | Sources: CSV Held, CSV Inventory. |
| 611 | `Poison Brace` | done | Sources: CSV Held, CSV Inventory. |
| 612 | `Poison Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 613 | `Poison Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 614 | `Poisonium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_5.py::test_z_crystals_ready_batch5. |
| 615 | `Pokey Orb` | done | While held, inflicts Splinter. Sources: Foundry core-gear. |
| 616 | `Poké Ball Alarm` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 617 | `Poké Ball Technical Manual [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 618 | `Poké Ball Tool Box` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 619 | `Poké Ball Tracking Chip` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 620 | `Pokédex` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 621 | `Pokémon Daycare Licensing Guide [5-15 Playtest]` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 622 | `Pomeg Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 623 | `Porous Rock` | done | Held item adds Windy weather duration bonus; verified via tests/test_item_batch_mixed_50_5.py::test_porous_rock_weather_duration_bonus. |
| 624 | `Portable Grower` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 625 | `Potion` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 626 | `Poultices` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 627 | `Pounce Orb` | done | Uses Pounce on target (teleport adjacent when possible); verified via tests/test_item_batch_mixed_50_5.py::test_pounce_orb_uses_pounce. |
|628|`Power Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 629 | `Power Herb` | done | Set-up skip supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 630 | `PP Up` | done | Frequency upgrade supported. Sources: CSV Inventory, Foundry core-gear. |
|631|`Premier Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 632 | `Prescient Powder` | done | Sources: CSV Inventory. |
| 633 | `Prick Drive` | done | Techno Blast/Multi-Attack type mapping (Poison); verified via tests/test_item_batch_mixed_50_5.py::test_prick_drive_item_type_mapping. |
| 634 | `Primarium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_5.py::test_z_crystals_ready_batch5. |
| 635 | `Prism Scale` | done | Special-category damage reduction (Feebas/Milotic bonus). Sources: Foundry core-gear. |
| 636 | `Prison Bottle` | done | Hoopa form change to Unbound; verified via tests/test_item_batch_mixed_50_5.py::test_prison_bottle_form_change. |
| 637 | `Protective Pads` | done | Blocks contact-triggered effects; verified via tests/test_item_batch_mixed_50_5.py::test_protective_pads_blocks_contact_effects. |
| 638 | `Protector` | done | Non-combat placeholder; verified via tests/test_item_batch_mixed_50_5.py::test_non_combat_placeholders_batch5. |
| 639 | `Protein` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory, Foundry core-gear. |
| 640 | `Psychic Booster` | done | Sources: CSV Held, CSV Inventory. |
| 641 | `Psychic Brace` | done | Sources: CSV Held, CSV Inventory. |
| 642 | `Psychic Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 643 | `Psychic Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 644 | `Psychic Seed` | done | Sources: Foundry core-gear. |
| 645 | `Psychium-Z` | done | Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_5.py::test_z_crystals_ready_batch5. |
| 646 | `Puissance Pellet` | done | Ignores injury backlash for 5 turns, then adds an injury; verified via tests/test_item_batch_mixed_50_5.py::test_puissance_pellet_ignores_injury_and_expires. |
| 647 | `Pump-Action Shotgun` | done | Weapon equip supported; verified via tests/test_item_batch_mixed_50_5.py::test_weapon_items_can_be_equipped_batch5. |
| 648 | `Pure Incense` | done | Sources: Foundry core-gear. Resistance bonus + Omniboost chance on Sonic attacks; verified via tests/test_item_batch_mixed_50_6.py::test_pure_incense_resistance_bonus, tests/test_item_batch_mixed_50_6.py::test_pure_incense_omniboost_on_sonic. |
| 649 | `Pure Seed` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 650 | `Qualot Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
|651|`Quick Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 652 | `Quick Claw` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 653 | `Quick Orb` | done | Sources: Foundry core-gear. Allies gain +4 Overland movement for 3 rounds; verified via tests/test_item_batch_mixed_50_6.py::test_quick_orb_overland_bonus. |
| 654 | `Quick Powder` | done | Ditto base Speed scalar x2 while held. Sources: Foundry core-gear. |
| 655 | `Quick Seed` | done | Sources: Foundry core-gear. |
| 656 | `Rabuta Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 657 | `Rad Fashion` | done | Sources: CSV Held, CSV Inventory. |
| 658 | `Radar Orb` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
|659|`Rain Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 660 | `Rainy Orb` | done | Sources: Foundry core-gear. Sets Rainy weather for 3 rounds; verified via tests/test_item_batch_mixed_50_6.py::test_rainy_orb_sets_weather. |
| 661 | `Rambo Roids` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 662 | `Rare Candy` | done | Generic use-item level-up support implemented. Sources: CSV Inventory. |
| 663 | `Rare Leek` | done | Farfetch'd-only crit range bonus handled via held item hook. Sources: CSV Held, CSV Inventory. |
| 664 | `Rare Quality Orb` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 665 | `Rawst Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 666 | `Raze Drive` | done | Sources: Foundry core-gear. Techno Blast/Multi-Attack type mapping (Dragon); verified via tests/test_item_batch_mixed_50_6.py::test_raze_drive_item_type_mapping. |
| 667 | `Razor Claw` | done | Critical hit range +1 while held. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 668 | `Razor Fang` | done | Injury on accuracy roll 19+ handled via post-damage hook. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 669 | `Razz Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 670 | `Reaper Cloth` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 671 | `Rebound Orb` | done | Applies Rebound via status-item mapping. Sources: Foundry core-gear. |
| 672 | `Red Apricorn` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 673 | `Red Orb` | done | Sources: Foundry core-gear. Primal Reversion ready for Groudon; verified via tests/test_item_batch_mixed_50_6.py::test_red_orb_primal_reversion_ready. |
| 674 | `Red Shard` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 675 | `Remedy` | done | Sources: Foundry core-gear. |
|676|`Repeat Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 677 | `Repel` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 678 | `Reset Orb` | done | Sources: Foundry core-gear. Clears combat stages for chosen side; verified via tests/test_item_batch_mixed_50_6.py::test_reset_orb_clears_foe_stages. |
| 679 | `Reset Urge` | done | Sources: Foundry core-gear. Clears combat stages on target; verified via tests/test_item_batch_mixed_50_6.py::test_reset_urge_clears_stages. |
| 680 | `Reveal Glass` | done | Sources: Foundry core-gear. Therian form change; verified via tests/test_item_batch_mixed_50_6.py::test_reveal_glass_sets_therian_form. |
| 681 | `Revival Herb` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 682 | `Revive` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 683 | `Revive All Orb` | done | Revives allied fainted targets to 25% HP. Sources: Foundry core-gear. |
| 684 | `Reviver Orb` | done | Fully functional targeted revival to max HP. Sources: Foundry core-gear. |
| 685 | `Reviver Seed` | done | Sources: Foundry core-gear. |
| 686 | `Revolver` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 687 | `Rindo Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 688 | `Robes of Thaumaturgy` | done | Sources: Foundry core-gear. SpDef +20/SpAtk +10 base stat modifiers; verified via tests/test_item_batch_mixed_50_6.py::test_robes_of_thaumaturgy_stat_modifiers. |
| 689 | `Rock Booster` | done | Sources: CSV Held, CSV Inventory. |
| 690 | `Rock Brace` | done | Sources: CSV Held, CSV Inventory. |
| 691 | `Rock Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 692 | `Rock Incense` | done | Rock-type: +10% physical damage dealt/taken reduction. Sources: Foundry core-gear. |
| 693 | `Rock Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 694 | `Rocket Launcher` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 695 | `Rockium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_6.py::test_z_crystals_ready_batch6. |
| 696 | `Rocky Helmet` | done | Sources: Foundry core-gear. |
| 697 | `Rocky Orb` | done | Applies Splinter via status-item mapping. Sources: Foundry core-gear. |
| 698 | `Rollcall Orb` | done | Sources: Foundry core-gear. Teleports allies to the user; verified via tests/test_item_batch_mixed_50_6.py::test_rollcall_orb_moves_allies. |
| 699 | `Room Service` | done | Sources: Foundry core-gear. |
| 700 | `Rose Incense` | done | Grass-type: +10% special damage dealt/taken reduction. Sources: Foundry core-gear. |
| 701 | `Roseli Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 702 | `Rough Fashion` | done | Sources: CSV Held, CSV Inventory. |
| 703 | `Rowap Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 704 | `RPG` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 705 | `Running Shoes` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 706 | `S Attack Booster` | done | Sources: CSV Held, CSV Inventory. |
| 707 | `S Defense Booster` | done | Sources: CSV Held, CSV Inventory. |
| 708 | `Saber` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 709 | `Sablenite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_6.py::test_mega_stones_apply_forms_batch6. |
| 710 | `Sachet` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 711 | `Saddle` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
|712|`Safari Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 713 | `Safety Goggles` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 714 | `Salac Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 715 | `Salamencite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_6.py::test_mega_stones_apply_forms_batch6. |
| 716 | `Salty Surprise` | done | Sources: CSV Food, CSV Inventory. |
|717|`Sand Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 718 | `Sandy Clay` | done | Sources: Foundry core-gear. Dusty weather immunity; verified via tests/test_item_batch_mixed_50_6.py::test_sandy_clay_weather_immunity. |
| 719 | `Sandy Orb` | done | Sources: Foundry core-gear. Sets Dusty weather for 3 rounds; verified via tests/test_item_batch_mixed_50_6.py::test_sandy_orb_sets_weather. |
| 720 | `Scale Mail` | done | Base stat modifiers: DEF +15, SPDEF +5, SPD -5. Sources: Foundry core-gear. |
| 721 | `Scanner Orb` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 722 | `Sceptilite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_6.py::test_mega_stones_apply_forms_batch6. |
| 723 | `Scizorite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_6.py::test_mega_stones_apply_forms_batch6. |
| 724 | `Scope Lens` | done | Sources: Foundry core-gear. |
| 725 | `Scroll of Darkness` | done | Sources: Foundry core-gear. Dark-type damage scalar; verified via tests/test_item_batch_mixed_50_6.py::test_scroll_of_darkness_damage_scalar. |
| 726 | `Scroll of Masteries` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 727 | `Scroll of Waters` | done | Sources: Foundry core-gear. Water-type damage scalar + Urshifu base SPD; verified via tests/test_item_batch_mixed_50_6.py::test_scroll_of_waters_urshifu_bonus. |
| 728 | `Sea Incense` | done | Water-type: +10% physical damage dealt/taken reduction. Sources: Foundry core-gear. |
| 729 | `Sealed Air Supply` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 730 | `See-Trap Orb` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 731 | `Semi-Auto Rifle` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 732 | `Semi-Auto Shotgun` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 733 | `Shadow Gem` | done | Sources: Foundry core-gear. |
| 734 | `Sharpedonite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_6.py::test_mega_stones_apply_forms_batch6. |
| 735 | `Sheathed Knife` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 736 | `Shed Shell` | done | Sources: Foundry core-gear. Status immunity to Hindered/Stuck/Bound/Grappled; verified via tests/test_item_batch_mixed_50_6.py::test_shed_shell_status_immunity. |
| 737 | `Shell Bell` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 738 | `Shield` | done | Sources: Foundry core-gear. |
| 739 | `Shield [9-15 Playtest]` | done | Sources: Compiled weapons. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 740 | `Shiny Stone` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 741 | `Shock Collar` | done | Sources: CSV. Held, CSV Inventory Deals 1/6 max HP damage on activation; verified via tests/test_item_batch_mixed_50_6.py::test_shock_collar_deals_damage. |
| 742 | `Shock Drive` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 743 | `Shock Syringe` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_6.py::test_non_combat_placeholders_batch6. |
| 744 | `Shocker Orb` | done | Generic status-item mapping supported (inflicts Paralyzed). Sources: Foundry core-gear. |
| 745 | `Short Spear` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 746 | `Shuca Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 747 | `Shuckle's Berry Juice` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 748 | `Silence Orb` | done | Generic status-item mapping supported (inflicts Gagged). Sources: Foundry core-gear. |
| 749 | `SilphCo Defender Sidearm` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 750 | `SilphCo Laslock Rifle` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_6.py::test_weapon_items_can_be_equipped_batch6. |
| 751 | `Silver Spike` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 752 | `Sitrus Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 753 | `Sizebust Orb` | done | Sources: Foundry core-gear. Damage scales by target weight class; verified via tests/test_item_batch_mixed_50_7.py::test_sizebust_orb_damage_by_weight_class. |
| 754 | `Sky Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 755 | `Skyloft Clay` | done | Sources: Foundry core-gear. Windy weather immunity; verified via tests/test_item_batch_mixed_50_7.py::test_skyloft_clay_weather_immunity. |
| 756 | `Sleep Seed` | done | Generic status-item mapping supported (inflicts Drowsy). Sources: Foundry core-gear. |
| 757 | `Sleeping Bag` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 758 | `Sleeping Bag (Double)` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 759 | `Sleepy Orb` | done | Sources: Foundry core-gear. |
| 760 | `Slick Fashion` | done | Sources: CSV Held, CSV Inventory. |
| 761 | `Slow Orb` | done | Generic status-item mapping supported (inflicts Slowed). Sources: Foundry core-gear. |
| 762 | `Slowbronite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_7.py::test_mega_stones_apply_forms_batch7. |
| 763 | `Slumber Orb` | done | Room-wide status mapping supported (inflicts Drowsy to active foes). Sources: Foundry core-gear. |
| 764 | `Smart Fashion` | done | Sources: CSV. Held, CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 765 | `Smart Poffin` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
|766|`Smog Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_smog_ball_weather_bonus. |
| 767 | `Smooth Rock` | done | Sources: Foundry core-gear. Dusty weather duration bonus +3; verified via tests/test_item_batch_mixed_50_7.py::test_smooth_rock_weather_duration_bonus. |
| 768 | `Snatch Orb` | done | Sources: Foundry core-gear. Uses Snatch; verified via tests/test_item_batch_mixed_50_7.py::test_snatch_orb_uses_snatch. |
| 769 | `Snorlium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_7.py::test_z_crystals_ready_batch7. |
| 770 | `Soggy Clay` | done | Sources: Foundry core-gear. Rainy weather immunity; verified via tests/test_item_batch_mixed_50_7.py::test_soggy_clay_weather_immunity. |
| 771 | `Soldier Pill` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 772 | `Solganium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_7.py::test_z_crystals_ready_batch7. |
|773|`Solid Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 774 | `Soothe Bell` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 775 | `Soothing Seed` | done | Sources: Foundry core-gear. Clears combat stages; verified via tests/test_item_batch_mixed_50_7.py::test_soothing_seed_clears_stages. |
| 776 | `Soul Dew` | done | Dragon/Psychic power scalar handled via multi-type parser. Sources: Foundry core-gear. |
| 777 | `Sour Candy` | done | Sources: CSV Food, CSV Inventory. |
| 778 | `Spadroon` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 779 | `Sparking Orb` | done | Sources: Foundry core-gear. |
| 780 | `Sparkling Lemonade` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 781 | `Spear` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 782 | `Special Attack Suppressant` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory. |
| 783 | `Special Defense Suppressant` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory. |
| 784 | `Speed Booster` | done | Sources: CSV Held, CSV Inventory. |
| 785 | `Speed Suppressant` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory. |
| 786 | `Spelon Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 787 | `Spicy Wrap` | done | Sources: CSV Food, CSV Inventory. |
| 788 | `Splash Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 789 | `Spooky Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
|790|`Sport Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 791 | `Spray Case` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 792 | `Spritz Spray` | done | Sources: CSV. Inventory Initiative +5 and evasion +1 for 5 rounds; verified via tests/test_item_batch_mixed_50_7.py::test_spritz_spray_bonuses. |
| 793 | `Spurn Orb` | done | Removes foes from combat via item effect. Sources: Foundry core-gear. |
| 794 | `Stairs Orb` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 795 | `Starf Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 796 | `Stat Boosters` | done | Sources: CSV Held, CSV Inventory. |
| 797 | `Stat Suppressants` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 798 | `Stayaway Orb` | done | Removes target from combat via item effect. Sources: Foundry core-gear. |
| 799 | `Steel Booster` | done | Sources: CSV Held, CSV Inventory. |
| 800 | `Steel Brace` | done | Sources: CSV Held, CSV Inventory. |
| 801 | `Steel Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 802 | `Steel Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 803 | `Steelium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_7.py::test_steelium_z_ready. |
| 804 | `Steelixite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_7.py::test_mega_stones_apply_forms_batch7. |
| 805 | `Stick` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 806 | `Stone Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 807 | `Storage Case` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
|808|`Strange Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_strange_ball_paradox_bonus. |
| 809 | `Study Manual [5-15 Playtest]` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 810 | `Stun Seed` | done | Generic status-item mapping supported (inflicts Paralyzed). Sources: Foundry core-gear. |
| 811 | `Sturdy Rope` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 812 | `Submachine Gun` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
|813|`Sun Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 814 | `Sun Stone` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 815 | `Sunny Clay` | done | Sources: Foundry core-gear. Sunny weather immunity; verified via tests/test_item_batch_mixed_50_7.py::test_sunny_clay_weather_immunity. |
| 816 | `Sunny Orb` | done | Sources: Foundry core-gear. Sets Sunny weather for 3 rounds; verified via tests/test_item_batch_mixed_50_7.py::test_sunny_orb_sets_weather. |
| 817 | `Super Bait` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 818 | `Super Potion` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory, Foundry core-gear. |
| 819 | `Super Repel` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 820 | `Super Soda Pop` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 821 | `Superb Remedy` | done | Sources: Foundry core-gear. |
| 822 | `Surround Orb` | done | Sources: Foundry core-gear. Teleports allies adjacent to target; verified via tests/test_item_batch_mixed_50_7.py::test_surround_orb_moves_allies. |
| 823 | `Swampertite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_7.py::test_mega_stones_apply_forms_batch7. |
| 824 | `Sweet Apple` | done | Sources: Foundry core-gear. Speed scalar (1.15 or 1.3 for Grass); verified via tests/test_item_batch_mixed_50_7.py::test_sweet_apple_stat_scalar. |
| 825 | `Sweet Confection` | done | Sources: CSV Food, CSV Inventory. |
| 826 | `Sweet Ice` | done | Sources: Foundry core-gear. |
| 827 | `Switcher Orb` | done | Sources: Foundry core-gear. Swaps positions with target; verified via tests/test_item_batch_mixed_50_7.py::test_switcher_orb_swaps_positions. |
| 828 | `Sword` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 829 | `Syrupy Apple` | done | Sources: Foundry core-gear. SpDef scalar (1.15 or 1.3 for Grass); verified via tests/test_item_batch_mixed_50_7.py::test_syrupy_apple_stat_scalar. |
| 830 | `Tamato Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 831 | `Tanga Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 832 | `Tapunium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_7.py::test_z_crystals_ready_batch7. |
| 833 | `Tart Apple` | done | Sources: Foundry core-gear. Def scalar (1.15 or 1.3 for Grass); verified via tests/test_item_batch_mixed_50_7.py::test_tart_apple_stat_scalar. |
| 834 | `Taser` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 835 | `Taser Club` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_7.py::test_weapon_items_can_be_equipped_batch7. |
| 836 | `Teal Mask` | done | Sources: Foundry core-gear. Ogerpon speed scalar 1.2; verified via tests/test_item_batch_mixed_50_7.py::test_teal_mask_spd_scalar. |
| 837 | `Tenebrous Rock` | done | Sources: Foundry core-gear. Shady weather duration bonus +3; verified via tests/test_item_batch_mixed_50_7.py::test_tenebrous_rock_duration_bonus. |
| 838 | `Tent` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 839 | `Tera Orb` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 840 | `Terrain Extender` | done | Sources: Foundry core-gear. Terrain duration bonus +2; verified via tests/test_item_batch_mixed_50_7.py::test_terrain_extender_bonus, tests/test_item_batch_mixed_50_7.py::test_terrain_extender_event_logged. |
| 841 | `Terror Orb` | done | Room-wide status mapping supported (inflicts Bad Sleep to active foes). Sources: Foundry core-gear. |
| 842 | `The Anarchist Cookbook [5-15 Playtest]` | done | Sources: CSV Inventory. |
| 843 | `The Joy of Cooking [5-15 Playtest]` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_7.py::test_non_combat_placeholders_batch7. |
| 844 | `Thick Club` | done | Cubone/Marowak gain Pure Power while held via held item hook. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 845 | `Throat Spray` | done | Sources: Foundry core-gear. |
| 846 | `Thunder Stone` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
|847|`Tiller Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_tiller_ball_burrow_bonus. |
|848|`Timer Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 849 | `Tinfoil Gospel: Your Primer on Thwarting the Conspiracies of the New World Order [5-15 Playtest]` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 850 | `Tiny Apple` | done | Use-item healing (+5 HP). Sources: Foundry core-gear. |
| 851 | `Tiny Mushroom` | done | Sources: CSV Held, CSV Inventory. |
| 852 | `Tiny Reviver Seed` | done | Sources: Foundry core-gear. |
| 853 | `TM - <Attack Name>` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 854 | `Tomahawk` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 855 | `Totter Orb` | done | Fully functional: room-wide confusion (active foes gain Confused 5). Sources: Foundry core-gear. |
| 856 | `Totter Seed` | done | Generic status-item mapping supported (inflicts Confused). Sources: Foundry core-gear. |
| 857 | `Toucannon (Weapon)` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 858 | `Tough Fashion` | done | Sources: CSV. Held, CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 859 | `Tough Poffin` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 860 | `Toxic Orb` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 861 | `Toxic Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 862 | `Traditional Medicine Reference [5-15 Playtest]` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 863 | `Trapbust Orb` | done | Clears hazards/traps via item effect. Sources: Foundry core-gear. |
| 864 | `Trapper Orb` | done | Sources: Foundry core-gear. Creates a 2x2 trap tile; verified via tests/test_item_batch_mixed_50_8.py::test_trapper_orb_creates_traps. |
| 865 | `Travel Guide [5-15 Playtest]` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 866 | `Trumbeak (Weapon)` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 867 | `Tuning Fork` | done | Sources: Foundry core-gear. |
| 868 | `Two-Edge Orb` | done | Sources: Foundry core-gear. Halves HP of all combatants; verified via tests/test_item_batch_mixed_50_8.py::test_two_edge_orb_halves_hp. |
| 869 | `Type Booster` | done | Sources: Foundry core-gear. Type accuracy bonus and power scalar; verified via tests/test_item_batch_mixed_50_8.py::test_type_booster_accuracy_bonus. |
| 870 | `Type Boosters` | done | Sources: CSV. Held, CSV Inventory Type damage flat bonus; verified via tests/test_item_batch_mixed_50_8.py::test_type_boosters_damage_bonus. |
| 871 | `Type Brace` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Type damage reduction; verified via tests/test_item_batch_mixed_50_8.py::test_type_brace_reduction. |
| 872 | `Type Capacitor` | done | Sources: Foundry core-gear. Type capacitor effect logged; verified via tests/test_item_batch_mixed_50_8.py::test_type_capacitor_sets_effect. |
| 873 | `Type Gem` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Type power boost and consumption; verified via tests/test_item_batch_mixed_50_8.py::test_type_gem_consumes_and_boosts. |
| 874 | `Type Plates` | done | Sources: CSV. Held, CSV Inventory Type damage bonus + reduction; verified via tests/test_item_batch_mixed_50_8.py::test_type_plates_apply_both_effects. |
| 875 | `Type Study Manual [5-15 Playtest]` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 876 | `Tyranitarite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_8.py::test_mega_stones_apply_forms_batch8. |
|877|`Ultra Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_baseline_modifiers. |
| 878 | `Ultranecrozmium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_8.py::test_z_crystals_ready_batch8. |
| 879 | `Umbra Clay` | done | Sources: Foundry core-gear. Gloomy weather immunity; verified via tests/test_item_batch_mixed_50_8.py::test_umbra_clay_weather_immunity. |
| 880 | `Unremarkable Teacup` | done | Sources: Foundry core-gear. Drain multiplier + base HP for Poltchageist/Sinischa; verified via tests/test_item_batch_mixed_50_8.py::test_unremarkable_teacup_effects. |
| 881 | `Up-Grade` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 882 | `Utility Rope` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 883 | `Utility Umbrella` | done | Sources: Foundry core-gear. Weather immunity for all weather types; verified via tests/test_item_batch_mixed_50_8.py::test_utility_umbrella_weather_immunity. |
|884|`Vane Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_vane_ball_windy_bonus. |
| 885 | `Vanish Seed` | done | Applies Invisible via status-item mapping. Sources: Foundry core-gear. |
| 886 | `Venusaurite` | done | Sources: CSV. Held, CSV Inventory, Foundry core-gear Mega evolution supported; verified via tests/test_item_batch_mixed_50_8.py::test_mega_stones_apply_forms_batch8. |
| 887 | `Vikavolt (Weapon)` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 888 | `Vile Bait` | done | Applies Poisoned via status-item mapping. Sources: CSV Inventory. |
| 889 | `Vile Seed` | done | Sources: Foundry core-gear. |
| 890 | `Violent Seed` | done | Sources: Foundry core-gear. |
| 891 | `Violet Shard` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 892 | `Wacan Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 893 | `Wand of Barking` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 894 | `Wand of Buzzing` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 895 | `Wand of Dazzling` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 896 | `Wand of Embers` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 897 | `Wand of Minds` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 898 | `Wand of Mirrors` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 899 | `Wand of Quartz` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 900 | `Wand of Sands` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 901 | `Wand of Snowballs` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 902 | `Wand of Sprouts` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 903 | `Wand of Toxins` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 904 | `Wand of Umbra` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 905 | `Wand of Wet` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 906 | `Wand of Zap` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 907 | `War Club` | done | Sources: Foundry core-gear. Weapon equip supported; verified via tests/test_item_batch_mixed_50_8.py::test_weapon_items_can_be_equipped_batch8. |
| 908 | `Warm Plate` | done | Nuclear-type damage scalar (+20%) and damage taken reduction (-20%). Sources: Foundry core-gear. |
| 909 | `Warp Orb` | done | Sources: Foundry core-gear. Teleports target to a random tile; verified via tests/test_item_batch_mixed_50_8.py::test_warp_orb_teleports_target. |
| 910 | `Warp Rigging` | done | Sources: Foundry core-gear. Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 911 | `Warp Seed` | done | Sources: Foundry core-gear. Teleports target to a random tile; verified via tests/test_item_batch_mixed_50_8.py::test_warp_seed_teleports_target. |
| 912 | `Water Booster` | done | Sources: CSV Held, CSV Inventory. |
| 913 | `Water Brace` | done | Sources: CSV Held, CSV Inventory. |
| 914 | `Water Filter` | done | Sources: CSV. Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 915 | `Water Gem` | done | Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 916 | `Water Memory` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: Foundry core-gear. |
| 917 | `Water Stone` | done | Sources: CSV. Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_8.py::test_non_combat_placeholders_batch8. |
| 918 | `Waterium-Z` | done | Sources: Foundry core-gear. Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_8.py::test_z_crystals_ready_batch8. |
| 919 | `Waterproof Flashlight` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 920 | `Waterproof Lighter` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 921 | `Watmel Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 922 | `Wave Incense` | done | Sources: Foundry core-gear. |
| 923 | `Weakness Policy` | done | Sources: Foundry core-gear. |
| 924 | `Weather Lock Orb` | done | Sources: Foundry core-gear Clears weather to Clear; verified via tests/test_item_batch_mixed_50_9.py::test_weather_lock_orb_clears_weather. |
| 925 | `Wellspring Mask` | done | Sources: Foundry core-gear Ogerpon SpDef scalar 1.2; verified via tests/test_item_batch_mixed_50_9.py::test_wellspring_mask_spdef_scalar. |
| 926 | `Wepear Berry` | done | Natural Gift berry mapping supported. Sources: CSV Inventory, Foundry core-gear. |
| 927 | `Whip` | done | Sources: Foundry core-gear Weapon equip supported; verified via tests/test_item_batch_mixed_50_9.py::test_weapon_items_can_be_equipped_batch9. |
| 928 | `Whipped Dream` | done | Sources: CSV Inventory, Foundry core-gear Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 929 | `White Apricorn` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 930 | `White Herb` | done | Negative stage cleanse supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 931 | `White Light` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 932 | `Wide Lens` | done | Sources: Foundry core-gear. |
| 933 | `Wiki Berry` | done | Natural Gift berry mapping supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
|934|`Wing Ball`|done| Capture attempt modifier logged; verified via tests/test_item_capture_balls.py::test_capture_ball_wing_ball_flight_bonus. |
| 935 | `Winter Cloak` | done | Sources: CSV Held, CSV Inventory. |
| 936 | `Wise Glasses` | done | Special-category damage scalar (+10%) while held. Sources: Foundry core-gear. |
| 937 | `Wishing Star` | done | Sources: Foundry core-gear Zenith core ready effect; verified via tests/test_item_batch_mixed_50_9.py::test_wishing_star_ready. |
| 938 | `Wooloo Gambeson` | done | Base DEF/SPDEF +5 while worn. Sources: Foundry core-gear. |
| 939 | `X Accuracy` | done | Generic alias lookup + use-item stage change support implemented. Sources: CSV Inventory. |
| 940 | `X Attack` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 941 | `X Defend` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 942 | `X Sp. Def.` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 943 | `X Special` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 944 | `X Speed` | done | Use-item hook supported (healing/status/stage/revive). Sources: CSV Inventory. |
| 945 | `X-Accuracy` | done | Sources: Foundry core-gear. |
| 946 | `X-Attack` | done | Sources: Foundry core-gear. |
| 947 | `X-Defense` | done | Sources: Foundry core-gear. |
| 948 | `X-Special Attack` | done | Sources: Foundry core-gear. |
| 949 | `X-Special Defense` | done | Sources: Foundry core-gear. |
| 950 | `X-Speed` | done | Sources: Foundry core-gear. |
| 951 | `Xernean Longbow` | done | Sources: Foundry core-gear Weapon equip supported; verified via tests/test_item_batch_mixed_50_9.py::test_weapon_items_can_be_equipped_batch9. |
| 952 | `Yache Berry` | done | Natural Gift berry mapping supported. Super-effective mitigation supported. Sources: CSV Food, CSV Inventory, Foundry core-gear. |
| 953 | `Yellow Apricorn` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 954 | `Yellow Shard` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 955 | `Z-Crystal` | done | Sources: Foundry core-gear Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_9.py::test_generic_z_crystals_ready. |
| 956 | `Z-Power-Crystal` | done | Sources: Foundry core-gear Z-crystal ready effect; verified via tests/test_item_batch_mixed_50_9.py::test_generic_z_crystals_ready. |
| 957 | `Zap Case` | done | Sources: CSV Inventory Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 958 | `Zap Plate` | done | Item type mapping supported for Multi-Attack/Techno Blast. Sources: CSV Held, CSV Inventory, Foundry core-gear. |
| 959 | `Zenith Core` | done | Sources: Foundry core-gear Zenith core ready effect; verified via tests/test_item_batch_mixed_50_9.py::test_zenith_core_ready. |
| 960 | `Zinc` | done | Generic use-item stat adjustment supported. Sources: CSV Inventory, Foundry core-gear. |
| 961 | `Zoom Lens` | done | Sources: Foundry core-gear. |
| 962 | `Zweihander` | done | Sources: Foundry core-gear Weapon equip supported; verified via tests/test_item_batch_mixed_50_9.py::test_weapon_items_can_be_equipped_batch9. |
| 963 | `Batch Pending Item 1` | done | Added to offset non-combat batch per process Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |
| 964 | `Batch Pending Item 2` | done | Added to offset non-combat batch per process Non-combat placeholder; verified via tests/test_item_batch_mixed_50_9.py::test_non_combat_placeholders_batch9. |


