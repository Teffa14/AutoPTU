# Attack Implementation Log

Master list of PTU moves sourced from `auto_ptu/data/compiled/moves.json`. This mirrors the Foundry data so we can track which attacks have bespoke hooks in our autonomous engine.

- **Total moves**: 856
- **Implemented**: 641
- **Pending**: 215

Status values: `pending` = no dedicated hook yet, `in progress` = actively implementing, `done` = code + tests + scenario coverage exist. The base attack pipeline already handles core damage math for every move; this table is for move-specific keywords/effects.

| # | Move | Category | Status | Notes |
|---|------|----------|--------|-------|
| 1 | `Absorb` | Special | done | Heals half the damage dealt and logs the absorption event. |
| 2 | `Accelerock` | Physical | done | Logs `accelerock_dash` so Dash priority is documented. |
| 3 | `Acid` | Special | done | Already handles the 10% SP. DEF drop for 5 activations on hit. |
| 4 | `Acid Armor` | Status | done | Set-up/resolution flow already recognized. |
| 5 | `Acid Spray` | Special | done | Lowers SP. DEF by -2 stages for five activations when it hits. |
| 6 | `Acrobatics` | Physical | done | No-item users gain +5 DB, lifting the effective base to 11. |
| 7 | `Acupressure` | Status | done | Roll 1d8 to buff Attack/Defense/S. Atk/S. Def/Speed/Accuracy (+2 CS), 8 picks the lowest stat. |
| 8 | `Aerial Ace` | Physical | done | Always-hit accuracy already handled upstream. |
| 9 | `Aeroblast` | Special | done | Even accuracy rolls now trigger criticals. |
| 10 | `After You` | Status | done | Schedules the target to act immediately after the caster. |
| 11 | `Agility` | Status | done | Increases Speed by +2 CS with an accompanying log event. |
| 12 | `Air Cutter` | Special | done | Rolls ≥18 become forced criticals and emit an event. |
| 13 | `Air Slash` | Special | done | Rolls ≥15 inflict Flinch on the defender. |
| 14 | `Ally Switch` | Status | done | Swaps the user/ally positions and logs the switch. |
| 15 | `Amnesia` | Status | done | Buffs Special Defense by +2 CS and records the change. |
| 16 | `Anchor Shot` | Physical | done | Requires the user to be on an Anchor Token; traps the target for 2 rounds. |
| 17 | `Ancient Power` | Special | done | Rolls ≥19 raise every combat stage by +1 CS. |
| 18 | `Apple Acid` | Special | done | Lowers the target's Special Defense by 1 CS on hit. |
| 19 | `Aqua Jet` | Physical | done | Logs the priority attack so the 1st-strike effect is recorded. |
| 20 | `Aqua Ring` | Status | done | Applies a healing coat that ticks each turn. |
| 21 | `Aqua Tail` | Physical | done | Records the pass-through strike in the log. |
| 22 | `Arcane Fury` | Special | done | Makes the target Vulnerable on rolls of 19+. |
| 23 | `Arcane Storm` | Special | done | Slows and makes each target Vulnerable for 1 round. |
| 24 | `Arm Thrust` | Physical | done | Five Strike handling already covers the multi-hit behavior. |
| 25 | `Aromatherapy` | Status | done | Cures one status from each ally. |
| 26 | `Aromatic Mist` | Status | done | Raises each ally’s SP. DEF by +1 CS. |
| 27 | `Assist` | Status | done | Selects an ally’s move and logs which one was borrowed. |
| 28 | `Assurance` | Physical | done | Boosts to DB 12 after the target has taken damage this round. |
| 29 | `Astonish` | Physical | done | Flinches on ≥15 rolls and auto-flinches unaware foes. |
| 30 | `Astral Barrage` | Special | done | Slows legal targets for one round on hit. |
| 31 | `Attack of Opportunity` | -- | done | Attack of Opportunity triggers are handled by the interrupt/shift logic. |
| 32 | `Attack Order` | Physical | done | Critical hit threshold lowered to 18+ with a logged crit roll. |
| 33 | `Attract` | Status | done | Infatuates only opposite-gender targets; fails vs same-gender/genderless. |
| 34 | `Aura Sphere` | Special | done | Cannot miss and already modeled via AC=None in the data. |
| 35 | `Aura Wheel` | Physical | done | Raises the user's Speed by +1 CS on hit. |
| 36 | `Aurora Beam` | Special | done | Lowers the target's Attack by -1 CS on rolls of 18+. |
| 37 | `Aurora Veil` | Status | done | Applies an Aurora Veil blessing to allies during hail. |
| 38 | `Autotomize` | Status | done | Raises the user's Speed by +2 CS. |
| 39 | `Avalanche` | Physical | done | Queues as a set-up move; DB 12 if the target damaged the user this round. |
| 40 | `Baby-Doll Eyes` | Status | done | Lowers the target's Attack by -1 CS. |
| 41 | `Backswing` | Physical | done | Enforces Large Melee Weapon requirement. |
| 42 | `Bane` | Special | done | Applies 3-turn tick damage and a -2 save penalty each turn. |
| 43 | `Baneful Bunker` | Status | done | Blocks the next hit and poisons melee attackers. |
| 44 | `Barb Barrage` | Physical | done | Poisons on 17+ and can auto-max Five Strike once per scene if the target has a status. |
| 45 | `Barrage` | Physical | done | Five Strike handling already covers the multi-hit behavior. |
| 46 | `Barrier` | Status | done | Places up to 4 barrier segments as blocking terrain on the grid. |
| 47 | `Bash!` | Physical | done | On 15+ rolls, sets the target's initiative to 0 next round. |
| 48 | `Baton Pass` | Status | done | Switches with an ally, transferring combat stages and coats. |
| 49 | `Beak Blast` | Physical | done | Declares a setup; burns melee attackers, then shifts and attacks at end of round. |
| 50 | `Beat Up` | Physical | done | Triggers adjacent allies to make Struggle attacks after the hit. |
| 51 | `Behemoth Bash` | Physical | done | DB increases by +2 per positive CS on the target, up to DB 20. |
| 52 | `Behemoth Blade` | Physical | done | DB increases by +2 per positive CS on the target, up to DB 20. |
| 53 | `Belch` | Special | done | Requires trading a Digestion/Food Buff earlier in the scene. |
| 54 | `Belly Drum` | Status | done | Cuts the user's HP to about 50% and raises Attack to +6 CS. |
| 55 | `Bestow` | Status | done | Transfers the user's held item or uses it on the target. |
| 56 | `Bide` | Physical | done | Stores damage taken, then releases it to adjacent foes. |
| 57 | `Bind` | Static | done | Applies Bind/Grappled/Trapped for 3 activations with tick damage. |
| 58 | `Bite` | Physical | done | Flinches the target on a 30% roll. |
| 59 | `Bitter Malice` | Special | done | Lowers the target's Attack by -1 CS for 5 activations. |
| 60 | `Blast Burn` | Special | done | Applies the Exhaust penalty for the following turn. |
| 61 | `Blaze Kick` | Physical | done | Burns the target on a 10% roll. |
| 62 | `Bleakwind Storm` | Special | done | Flinches on 15+ and freezes on 19+. |
| 63 | `Bleed!` | Physical | done | Applies Bleed for 3 turns, ticking damage each turn. |
| 64 | `Blind` | Status | done | Stealth contest can inflict Blinded for 1 activation. |
| 65 | `Blizzard` | Special | done | Freezes on 15+ and cannot miss during hail. |
| 66 | `Block` | Status | done | Leaves the target Stuck and Trapped until the user's next turn. |
| 67 | `Blue Flare` | Special | done | Burns on 17+. |
| 68 | `Body Press` | Physical | done | Uses the user's Defense for damage calculation. |
| 69 | `Body Slam` | Physical | done | Paralyzes the target on rolls of 15+. |
| 70 | `Bolt Beak` | Physical | done | Deals +10 damage against lower-initiative targets that have not acted. |
| 71 | `Bolt Strike` | Physical | done | Status tracking already implemented in battle hooks. |
| 72 | `Bon Mot` | Status | done | Guile contest enrages the target and blocks AP-spend (At-Will only) for 1 round. |
| 73 | `Bone Club` | Physical | done | Flinches the target on rolls of 18+. |
| 74 | `Bone Rush` | Physical | done | Five Strike handling already covers the multi-hit behavior. |
| 75 | `Bonemerang` | Physical | done | Strike handling already covers the multi-hit behavior. |
| 76 | `Boomburst` | Special | done | No special hook beyond baseline resolution. |
| 77 | `Bounce` | Physical | done | Applies Vulnerable and paralyzes on rolls of 16+. |
| 78 | `Branch Poke` | Physical | done | No special hook beyond baseline resolution. |
| 79 | `Brave Bird` | Physical | done | Recoil handling already covers the user damage. |
| 80 | `Breaking Swipe` | Physical | done | Lowers the target's Attack by -1 CS. |
| 81 | `Brick Break` | Physical | done | Shatters Reflect and Light Screen on hit. |
| 82 | `Brine` | Special | done | DB increases to 13 when the target is at or below half HP. |
| 83 | `Brutal Swing` | Physical | done | No special hook beyond baseline resolution. |
| 84 | `Bubble` | Special | done | Lowers Speed by -1 CS on 16+ rolls. |
| 85 | `Bubblebeam` | Special | done | Lowers Speed by -1 CS on 18+ rolls. |
| 86 | `Bug Bite` | Physical | done | Steals a food buff from the target. |
| 87 | `Bug Buzz` | Special | done | Special move resolution already handles its effects. |
| 88 | `Bulk Up` | Status | done | Raises Attack and Defense by +1 CS. |
| 89 | `Bulldoze` | Physical | done | Lowers Speed by -1 CS on each hit target. |
| 90 | `Bullet Punch` | Physical | done | Logs the priority attack so the 1st-strike effect is recorded. |
| 91 | `Bullet Seed` | Physical | done | Five Strike handling already covers the multi-hit behavior. |
| 92 | `Bullseye` | Physical | done | Critical hit threshold lowered to 16+ when the attack lands. |
| 93 | `Burn Up` | Special | done | Removes the user's Fire typing after resolving. |
| 94 | `Burning Jealousy` | Special | done | Burns nearby foes with raised combat stages once per scene. |
| 95 | `Calm Mind` | Status | done | Raises Special Attack and Special Defense by +1 CS. |
| 96 | `Camouflage` | Status | done | Changes the user's type to match weather-based terrain defaults. |
| 97 | `Captivate` | Status | done | Lowers Special Attack by -2 CS against opposite-gender targets. |
| 98 | `Ceaseless Edge` | Physical | done | Crits on 19+ and applies a Vortex trap with tick damage. |
| 99 | `Charge` | Status | done | Raises Special Defense by +1 CS and boosts the next Electric attack. |
| 100 | `Charge Beam` | Special | done | On hit, rolls 1d20 and raises the user's Special Attack by +1 CS on 7+. |
| 101 | `Charm` | Status | done | Lowers the target's Attack by -2 CS. |
| 102 | `Chatter` | Special | done | Confuses targets on 16+ rolls. |
| 103 | `Cheap Shot` | Physical | done | Priority strike handled by existing hooks. |
| 104 | `Chip Away` | Physical | done | Ignores defense stages and damage reduction for this attack. |
| 105 | `Chloroblast` | Special | done | Recoil handling already covers the user damage. |
| 106 | `Circle Throw` | Physical | done | Forced movement handling already covers the push effect. |
| 107 | `Clamp` | Static | done | Grants grapple contest bonuses and deals a tick on gaining dominance. |
| 108 | `Clanging Scales` | Special | done | Adds half Defense to damage and lowers the user's Defense by -1 CS. |
| 109 | `Clangorous Soul` | Status | done | Costs 1/3 max HP and raises all combat stages by +1 CS. |
| 110 | `Clear Smog` | Special | done | Resets the target's combat stages after hit. |
| 111 | `Close Combat` | Physical | done | Lowers the user's Defense and Special Defense by -1 CS after damage. |
| 112 | `Coaching` | Status | done | Raises the user's and nearby allies' Attack and Defense by +1 CS. |
| 113 | `Coil` | Status | done | Raises Attack, Defense, and Accuracy by +1 CS. |
| 114 | `Comet Punch` | Physical | done | Five Strike handling already covers the multi-hit behavior. |
| 115 | `Cone of Force` | Special | done | Area resolution already covers the cone effect. |
| 116 | `Confide` | Status | done | Lowers the target's Special Attack by -1 CS. |
| 117 | `Confuse Ray` | Status | done | Inflicts Confused. |
| 118 | `Confusion` | Special | done | Confuses the target on 19+ rolls. |
| 119 | `Constrict` | Physical | done | Lowers Speed by -1 CS and allows swift use while grappling. |
| 120 | `Conversion` | Status | done | Changes the user's type to a known move's elemental type. |
| 121 | `Conversion2` | Status | done | Changes the user's type to a move type that resists the last damage taken. |
| 122 | `Copycat` | Status | done | Copycat resolves the target's last move. |
| 123 | `Core Enforcer` | Special | done | Disables a chosen target ability until the end of the encounter. |
| 124 | `Corrosive Gas` | Status | done | Disables held items for the scene and suppresses Steel's poison immunity. |
| 125 | `Cosmic Power` | Status | done | Raises Defense and Special Defense by +1 CS. |
| 126 | `Cotton Guard` | Status | done | Raises Defense by +3 CS. |
| 127 | `Cotton Spore` | Status | done | Lowers Speed by -2 CS. |
| 128 | `Counter` | Physical | done | Counter logic already implemented with damage reflection. |
| 129 | `Court Change` | Status | done | Swaps hazards across the field and swaps team blessings. |
| 130 | `Covet` | Physical | done | Steals a held item if the user isn't holding one. |
| 131 | `Crabhammer` | Physical | done | Critical hit threshold lowered to 18+. |
| 132 | `Crafty Shield` | Status | done | Blocks incoming status moves for nearby allies as an interrupt. |
| 133 | `Cross Chop` | Physical | done | Critical hit threshold lowered to 16+. |
| 134 | `Cross Poison` | Physical | done | Critical hit threshold lowered to 18+ and poisons on 19+. |
| 135 | `Crunch` | Physical | done | Lowers Defense by -1 CS on 17+. |
| 136 | `Crush Claw` | Physical | done | Lowers Defense by -1 CS on even-numbered rolls. |
| 137 | `Crush Grip` | Physical | done | Damage base scales down by 1 per 10% missing HP on the target. |
| 138 | `Curse` | Status | done | Ghost users lose 1/3 max HP to curse a target; non-ghosts raise Attack/Defense and lower Speed. |
| 139 | `Cut` | Physical | done | Ignores up to 5 damage reduction. |
| 140 | `Dark Pulse` | Special | done | Flinches the target on 17+. |
| 141 | `Dark Void` | Status | done | Puts the target to sleep. |
| 142 | `Dark Void [SM]` | Status | done | Puts the target to sleep. |
| 143 | `Darkest Lariat` | Physical | done | Ignores positive Defense stages and damage reduction. |
| 144 | `Dazzling Gleam` | Special | done | No special hook beyond baseline resolution. |
| 145 | `Deadly Strike` | Physical | done | Always critical hit when it connects. |
| 146 | `Decorate` | Status | done | Raises the target's Attack and Special Attack by +2 CS. |
| 147 | `Defend Order` | Status | done | Raises Defense and Special Defense by +1 CS. |
| 148 | `Defense Curl` | Status | done | Applies Curled Up, granting crit immunity, damage reduction, and accuracy penalty. |
| 149 | `Defog` | Status | done | Clears weather, hazards, and coats. |
| 150 | `Destiny Bond` | Status | done | Binds targets and KOs them if they KO the user before next turn. |
| 151 | `Detect` | Status | done | Auto-triggers on hit to negate the incoming move as a scene reaction. |
| 152 | `Diamond Storm` | Physical | done | Defense boost handled on hit. |
| 153 | `Dig` | Physical | done | Set-up/resolution flow already recognized. |
| 154 | `Dire Claw` | Physical | done | Inflicts Poisoned/Paralyzed/Flinch on 15+ rolls. |
| 155 | `Dirty Trick` | Status | done | Uses Hinder, Blind, then Low Blow contests once per target each scene. |
| 156 | `Disable` | Status | done | Auto-triggers on hit to disable the attacker's move; manual use targets last move. |
| 157 | `Disarm` | Status | done | Combat/Stealth contest can drop the target's held item; Telekinetic focus works at range. |
| 158 | `Disarming Voice` | Special | done | Never-miss handling already covered. |
| 159 | `Discharge` | Special | done | Paralyzes targets on 15+ rolls. |
| 160 | `Disengage` | -- | done | Shifts 1 meter without provoking attacks of opportunity. |
| 161 | `Dive` | Physical | done | Set-up/resolution flow already recognized. |
| 162 | `Dizzy Punch` | Physical | done | Confuses the target on 17+ rolls. |
| 163 | `Doom Desire` | Special | done | Delayed hit resolution already implemented. |
| 164 | `Double Hit` | Physical | done | Implemented via explicit hook or generic handling. |
| 165 | `Double Iron Bash` | Physical | done | Implemented via explicit hook or generic handling. |
| 166 | `Double Kick` | Physical | done | Implemented via explicit hook or generic handling. |
| 167 | `Double Slap` | Physical | done | Implemented via explicit hook or generic handling. |
| 168 | `Double Swipe` | Physical | done | Implemented via explicit hook or generic handling. |
| 169 | `Double Team` | Status | done | Grants 3 activations that boost accuracy or evasion by +2. |
| 170 | `Double-Edge` | Physical | done | Implemented via explicit hook or generic handling. |
| 171 | `Draco Meteor` | Special | done | Implemented via explicit hook or generic handling. |
| 172 | `Dragon Ascent` | Physical | done | Lowers the user's Defense and Special Defense by -1 CS. |
| 173 | `Dragon Breath` | Special | done | Paralyzes the target on 15+. |
| 174 | `Dragon Claw` | Physical | done | No special hook beyond baseline resolution. |
| 175 | `Dragon Dance` | Status | done | Raises the user's Attack and Speed by +1 CS. |
| 176 | `Dragon Darts` | Physical | done | Implemented via explicit hook or generic handling. |
| 177 | `Dragon Energy` | Special | done | Damage base drops by 1 per 10% missing HP. |
| 178 | `Dragon Hammer` | Physical | done | No special hook beyond baseline resolution. |
| 179 | `Dragon Pulse` | Special | done | No special hook beyond baseline resolution. |
| 180 | `Dragon Rage` | Special | done | Deals fixed 15 HP damage on hit. |
| 181 | `Dragon Rush` | Physical | done | Implemented via explicit hook or generic handling. |
| 182 | `Dragon Tail` | Physical | done | Implemented via explicit hook or generic handling. |
| 183 | `Drain Punch` | Physical | done | Heals the user for half the damage dealt. |
| 184 | `Draining Kiss` | Special | done | Heals the user for half the damage dealt. |
| 185 | `Dream Eater` | Special | done | Only affects sleeping targets, heals half damage, and does not wake them. |
| 186 | `Drill Peck` | Physical | done | No special hook beyond baseline resolution. |
| 187 | `Drill Run` | Physical | done | Critical hit threshold lowered to 18+. |
| 188 | `Drum Beating` | Physical | done | Lowers the target's Speed by -1 CS. |
| 189 | `Dual Chop` | Physical | done | Implemented via explicit hook or generic handling. |
| 190 | `Dual Wingbeat` | Physical | done | Implemented via explicit hook or generic handling. |
| 191 | `Dynamax Cannon` | Special | done | DB increases by +2 per positive CS on the target, up to DB 20. |
| 192 | `Dynamic Punch` | Physical | done | Confuses the target and ignores evasion if the target is flanked. |
| 193 | `Earth Power` | Special | done | Lowers Special Defense by -1 CS on 16+. |
| 194 | `Earthquake` | Physical | done | Can hit underground targets (Dig). |
| 195 | `Echoed Voice` | Special | done | Damage base scales with Echoed Voice usage in the prior rounds. |
| 196 | `Eerie Impulse` | Status | done | Lowers the target's Special Attack by -2 CS. |
| 197 | `Eerie Spell` | Special | done | Once per scene, disables the target's last move used. |
| 198 | `Egg Bomb` | Physical | done | No special hook beyond baseline resolution. |
| 199 | `Electric Terrain` | Status | done | Electrifies the field for 5 rounds; grounded Electric attacks gain +10 damage and grounded targets are immune to Sleep. |
| 200 | `Electrify` | Status | done | Forces damaging Water or Melee attacks to become Electric until end of the user's next turn. |
| 201 | `Electro Ball` | Special | done | Adds user Speed and target Speed into the damage calculation. |
| 202 | `Electroweb` | Special | done | Lowers Speed by -1 CS on all targets hit. |
| 203 | `Embargo` | Status | done | Disables held items for the encounter; only one target at a time. |
| 204 | `Ember` | Special | done | Burns the target on 18+. |
| 205 | `Encore` | Status | done | Roll 1d6 to apply Confused, Suppressed, or Enraged. |
| 206 | `Endeavor` | Physical | done | Deals tick damage equal to the user's injury count. |
| 207 | `Endure` | Status | done | Grants Endure to leave the user at 1 HP if a hit would KO them. |
| 208 | `Energy Ball` | Special | done | Lowers the target's Special Defense by -1 CS on 17+. |
| 209 | `Energy Blast` | Special | done | Raises the user's Special Attack by +1 CS on 19+. |
| 210 | `Energy Sphere` | Special | done | Raises the user's Special Defense by +1 CS on 19+. |
| 211 | `Energy Vortex` | Special | done | Applies Vortex and Trapped. |
| 212 | `Entrainment` | Status | done | Grants one of the user's abilities for 3 turns. |
| 213 | `Eruption` | Special | done | Damage base drops by 1 per 10% missing HP. |
| 214 | `Esper Wing` | Special | done | Critical hit threshold lowered to 18+. |
| 215 | `Eternabeam` | Special | done | Implemented via explicit hook or generic handling. |
| 216 | `EW Adept` | -- | done | No special hook beyond baseline resolution. |
| 217 | `EW Expert` | -- | done | No special hook beyond baseline resolution. |
| 218 | `Expanding Force` | Special | done | Creates Psychic Terrain in a Burst 7 for 5 rounds once per scene. |
| 219 | `Explosion` | Physical | done | User loses HP equal to current HP plus 50% max HP. |
| 220 | `Extrasensory` | Special | done | Flinches the target on 19+. |
| 221 | `Extreme Speed` | Physical | done | Logs the priority attack so the 1st-strike effect is recorded. |
| 222 | `Facade` | Physical | done | DB doubles to 14 when the user has a persistent status affliction. |
| 223 | `Fairy Lock` | Status | done | Traps and slows legal targets while the user remains on the field. |
| 224 | `Fairy Wind` | Special | done | No special hook beyond baseline resolution. |
| 225 | `Fake Out` | Physical | done | On the join turn, resolves with Priority and flinches the target. |
| 226 | `Fake Tears` | Status | done | Lowers the target's Special Defense by -2 CS on hit. |
| 227 | `False Surrender` | Physical | done | Implemented via explicit hook or generic handling. |
| 228 | `False Swipe` | Physical | done | Never drops the target below 1 HP. |
| 229 | `Façade` | Physical | done | DB doubles to 14 when the user has a persistent status affliction. |
| 230 | `Feather Dance` | Status | done | Lowers every legal target's Attack by -2 Combat Stages. |
| 231 | `Feint` | Status | done | Bypasses and removes shielding effects on the target. |
| 232 | `Feint Attack` | Physical | done | Implemented via explicit hook or generic handling. |
| 233 | `Fell Stinger` | Physical | done | Raises the user's Attack by +2 CS after it knocks out the target. |
| 234 | `Fell Stinger [SM]` | Physical | done | Raises the user's Attack by +2 CS after it knocks out the target. |
| 235 | `Fiery Dance` | Special | done | Raises the user's Special Attack by +1 CS on even-numbered rolls. |
| 236 | `Fiery Wrath` | Special | done | Flinches the target on 17+ and may be used as Fire once per scene. |
| 237 | `Final Gambit` | Special | done | Self-faints (HP set to 0) and then deals damage equal to the HP lost, ignoring item triggers. |
| 238 | `Fire Blast` | Special | done | Burns the target on rolls of 19+. |
| 239 | `Fire Fang` | Physical | done | Burns or Flinches on rolls of 18-19 (coin flip) and both on 20, logging both status events. |
| 240 | `Fire Lash` | Physical | done | Lowers the target's Defense by -1 CS when it hits. |
| 241 | `Fire Pledge` | Special | done | Tracks pledge combos; Fire+Grass creates fire hazards, Fire+Water creates Rainbow. |
| 242 | `Fire Punch` | Physical | done | Burns the target on rolls of 19+. |
| 243 | `Fire Spin` | Special | done | Applies Vortex and Trapped for 3 rounds on hit. |
| 244 | `First Impression` | Physical | done | On the join turn, resolves with Priority and flinches the target. |
| 245 | `Fishious Rend` | Physical | done | Bonus +10 damage versus lower-initiative foes (tracked by fishious_rend_bonus). |
| 246 | `Fissure` | Status | done | Rolls 1d100 versus 30 + level difference to instantly faint the foe; the log records the roll amount. |
| 247 | `Flail` | Physical | done | DB increases by +1 per injury on the user. |
| 248 | `Flame Burst` | Special | done | Adjacent allies that are cardinally adjacent to the target lose 5 HP when the hit lands. |
| 249 | `Flame Charge` | Physical | done | Raises the user's Speed by +1 Combat Stage after resolving. |
| 250 | `Flame Wheel` | Physical | done | Burns the target on rolls of 19+. |
| 251 | `Flamethrower` | Special | done | Burns the target on rolls of 19+. |
| 252 | `Flare Blitz` | Physical | done | Burns the target on rolls of 19+ plus applies the usual recoil handling (logged separately). |
| 253 | `Flash` | Status | done | Lowers every legal target's Accuracy by -1. |
| 254 | `Flash Cannon` | Special | done | Lowers the target's Special Defense by -1 CS on rolls of 17+. |
| 255 | `Flatter` | Status | done | Raises the target's Special Attack by +1 CS and confuses them. |
| 256 | `Fleur Cannon` | Special | done | Implemented via explicit hook or generic handling. |
| 257 | `Fling` | Physical | done | Consumes the held item and logs the thrown item. |
| 258 | `Flip Turn` | Physical | done | Switches the user out after dealing damage; ignores Trapped. |
| 259 | `Flirt` | Status | done | Infatuates the target (charm check not modeled). |
| 260 | `Floral Healing` | Status | done | Heals 1/2 max HP or 2/3 in Grassy Terrain. |
| 261 | `Flower Shield` | Status | done | Raises Defense of Grass-type targets by +2 CS. |
| 262 | `Fly` | Physical | done | Implemented via explicit hook or generic handling. |
| 263 | `Flying Press` | Physical | done | Chooses Fighting or Flying type damage based on effectiveness. |
| 264 | `Flying Press [SM]` | Physical | done | Chooses Fighting or Flying type damage based on effectiveness. |
| 265 | `Focus Blast` | Special | done | Implemented via explicit hook or generic handling. |
| 266 | `Focus Energy` | Status | done | Applies Pumped and extends the critical range by 2 until switching. |
| 267 | `Focus Punch` | Physical | done | Set-up move; fails if user takes 25%+ max HP damage before resolving. |
| 268 | `Follow Me` | Status | done | Redirects foes to the user until the end of the next turn. |
| 269 | `Force Palm` | Physical | done | Paralyzes the target on 18+. |
| 270 | `Foresight` | Status | done | For the rest of the turn, Normal/Fighting moves can hit Ghosts. |
| 271 | `Forest's Curse` | Status | done | Adds the Grass type for 5 turns. |
| 272 | `Foul Play` | Physical | done | Uses the target's Attack stat for damage. |
| 273 | `Freeze Shock` | Physical | done | Implemented via explicit hook or generic handling. |
| 274 | `Freeze-Dry` | Special | done | Treats Water as weak to Ice when calculating effectiveness. |
| 275 | `Freezing Glare` | Special | done | Freezes on 19+ and may switch to Ice type once per scene. |
| 276 | `Frenzy Plant` | Special | done | Implemented via explicit hook or generic handling. |
| 277 | `Frost Breath` | Special | done | Always crits if it hits. |
| 278 | `Frustration` | Physical | done | DB becomes 9 minus the user's Loyalty value. |
| 279 | `Furious Strikes` | Physical | done | Implemented via explicit hook or generic handling. |
| 280 | `Fury Attack` | Physical | done | Implemented via explicit hook or generic handling. |
| 281 | `Fury Cutter` | Physical | done | DB scales with consecutive hits and resets on miss/no damage. |
| 282 | `Fury Swipes` | Physical | done | Implemented via explicit hook or generic handling. |
| 283 | `Fusion Bolt` | Physical | done | Implemented via explicit hook or generic handling. |
| 284 | `Fusion Flare` | Special | done | Implemented via explicit hook or generic handling. |
| 285 | `Future Sight` | Special | done | Implemented via explicit hook or generic handling. |
| 286 | `Gastro Acid` | Status | done | Suppresses one of the target's abilities for the encounter. |
| 287 | `Gear Grind` | Physical | done | Implemented via explicit hook or generic handling. |
| 288 | `Gear Up` | Status | done | Plus/Minus targets gain +1 Attack and Special Attack. |
| 289 | `Gear Up [SS]` | Status | done | Steel-typed targets gain +1 Attack and Special Attack. |
| 290 | `Geomancy` | Status | done | Implemented via explicit hook or generic handling. |
| 291 | `Giga Drain` | Special | done | Heals half the damage dealt. |
| 292 | `Giga Impact` | Physical | done | Implemented via explicit hook or generic handling. |
| 293 | `Glacial Lance` | Physical | done | Implemented via explicit hook or generic handling. |
| 294 | `Glaciate` | Special | done | Lowers Speed by -1 CS and even rolls slow grounded targets. |
| 295 | `Glare` | Status | done | Paralyzes the target on hit. |
| 296 | `Gouge` | Physical | done | Implemented via explicit hook or generic handling. |
| 297 | `Grapple` | Status | done | Uses the grapple contest and applies Grappled/Vulnerable on success. |
| 298 | `Grass Knot` | Special | done | DB equals twice the target's Weight Class. |
| 299 | `Grass Pledge` | Special | done | Tracks pledge combos; fire creates hazards, water slows and -2 Speed. |
| 300 | `Grass Whistle` | Status | done | Puts the target to Sleep. |
| 301 | `Grassy Glide` | Physical | done | Priority on Grassy Terrain; may create Grassy Terrain after hit. |
| 302 | `Grassy Terrain` | Status | done | Creates Grassy Terrain for 5 rounds. |
| 303 | `Grav Apple` | Physical | done | Lowers the target's Defense by -1 CS. |
| 304 | `Gravity` | Status | done | Creates Gravity/Warped terrain for 5 rounds with +2 accuracy. |
| 305 | `Growl` | Status | done | Lowers Attack by -1 CS on hit. |
| 306 | `Growth` | Status | done | Raises Attack and Special Attack; doubled in sun. |
| 307 | `Grudge` | Status | done | Marks the user to Suppress the attacker after a KO (interrupt style). |
| 308 | `Guard Split` | Status | done | Applies -5 DEF/SPDEF stat modifiers to the target and 5 damage reduction to the user. |
| 309 | `Guard Swap` | Status | done | Swaps Defense and Special Defense combat stages between user and target. |
| 310 | `Guillotine` | Status | done | Rolls a level-based d100 check to faint the target. |
| 311 | `Gunk Shot` | Physical | done | Implemented via explicit hook or generic handling. |
| 312 | `Gust` | Special | done | Boosts DB against Fly/Sky Drop targets and logs the airborne hit. |
| 313 | `Gyro Ball` | Physical | done | Adds bonus damage based on Speed difference. |
| 314 | `Hail` | Status | done | Sets Hail weather and logs the weather change. |
| 315 | `Hammer Arm` | Physical | done | Lowers the user's Speed by -1 CS on hit. |
| 316 | `Harden` | Status | done | Raises the user's Defense by +1 CS. |
| 317 | `Haze` | Status | done | Resets combat stages for all combatants. |
| 318 | `Head Charge` | Physical | done | Implemented via explicit hook or generic handling. |
| 319 | `Head Smash` | Physical | done | Implemented via explicit hook or generic handling. |
| 320 | `Headbutt` | Physical | done | Flinches on 15+ rolls. |
| 321 | `Headlong Rush` | Physical | done | Implemented via explicit hook or generic handling. |
| 322 | `Heal Bell` | Status | done | Cures persistent status ailments in range. |
| 323 | `Heal Block` | Status | done | Prevents healing until the target switches or takes a breather. |
| 324 | `Heal Order` | Status | done | Heals 50% of max HP. |
| 325 | `Heal Pulse` | Status | done | Heals 50% of max HP on a non-self target. |
| 326 | `Healing Wish` | Status | done | User faints to restore target HP, injuries, and move frequency. |
| 327 | `Heart Stamp` | Physical | done | Flinches on 15+ rolls. |
| 328 | `Heart Swap` | Status | done | Swaps combat stages between user and target. |
| 329 | `Heat Crash` | Physical | done | Damage base scales with weight class difference. |
| 330 | `Heat Wave` | Special | done | Implemented via explicit hook or generic handling. |
| 331 | `Heavy Slam` | Physical | done | Damage base scales with weight class difference. |
| 332 | `Helping Hand` | Status | done | Grants +2 accuracy and +10 damage to the target's next attack this round. |
| 333 | `Hex` | Special | done | Once per scene, increases DB to 13 versus afflicted targets. |
| 334 | `Hidden Power` | Special | done | Assigns and persists Hidden Power's elemental type. |
| 335 | `Hidden Power Bug` | Special | done | Typed variant uses base data; no special hook needed. |
| 336 | `Hidden Power Dark` | Special | done | Typed variant uses base data; no special hook needed. |
| 337 | `Hidden Power Dragon` | Special | done | Typed variant uses base data; no special hook needed. |
| 338 | `Hidden Power Electric` | Special | done | Typed variant uses base data; no special hook needed. |
| 339 | `Hidden Power Fairy` | Special | done | Typed variant uses base data; no special hook needed. |
| 340 | `Hidden Power Fighting` | Special | done | Typed variant uses base data; no special hook needed. |
| 341 | `Hidden Power Fire` | Special | done | Typed variant uses base data; no special hook needed. |
| 342 | `Hidden Power Flying` | Special | done | Typed variant uses base data; no special hook needed. |
| 343 | `Hidden Power Ghost` | Special | done | Typed variant uses base data; no special hook needed. |
| 344 | `Hidden Power Grass` | Special | done | Typed variant uses base data; no special hook needed. |
| 345 | `Hidden Power Ground` | Special | done | Typed variant uses base data; no special hook needed. |
| 346 | `Hidden Power Ice` | Special | done | Typed variant uses base data; no special hook needed. |
| 347 | `Hidden Power Poison` | Special | done | Typed variant uses base data; no special hook needed. |
| 348 | `Hidden Power Psychic` | Special | done | Typed variant uses base data; no special hook needed. |
| 349 | `Hidden Power Rock` | Special | done | Typed variant uses base data; no special hook needed. |
| 350 | `Hidden Power Steel` | Special | done | Typed variant uses base data; no special hook needed. |
| 351 | `Hidden Power Water` | Special | done | Typed variant uses base data; no special hook needed. |
| 352 | `High Horsepower` | Physical | done | Sprint usage grants Smite and logs the sprint follow-up. |
| 353 | `High Jump Kick` | Physical | done | Miss recoil (1/4 max HP) unless blocked by a shield; blocked under Gravity. |
| 354 | `Hinder` | Status | done | Opposed Athletics contest applies Slowed and Hindered for 1 round. |
| 355 | `Hold Hands` | Status | done | Applies Cheered to both combatants and grants 3 ticks of temp HP. |
| 356 | `Hone Claws` | Status | done | Raises Attack and Accuracy by +1 CS. |
| 357 | `Horn Attack` | Physical | done | No special hook beyond baseline resolution. |
| 358 | `Horn Drill` | Status | done | D100 execute check based on level difference. |
| 359 | `Horn Leech` | Physical | done | Drains half the damage dealt. |
| 360 | `Howl` | Status | done | Raises the user's Attack by +1 CS. |
| 361 | `Howl [SS]` | Status | done | Burst 1 allies gain +1 Attack CS. |
| 362 | `Hurricane` | Special | done | Implemented via explicit hook or generic handling. |
| 363 | `Hydro Cannon` | Special | done | Implemented via explicit hook or generic handling. |
| 364 | `Hydro Pump` | Special | done | Implemented via explicit hook or generic handling. |
| 365 | `Hyper Beam` | Special | done | Implemented via explicit hook or generic handling. |
| 366 | `Hyper Fang` | Physical | done | Flinches the target on 19+. |
| 367 | `Hyper Voice` | Special | done | Implemented via explicit hook or generic handling. |
| 368 | `Hyperspace Fury` | Physical | done | Bypasses interrupts and lowers the user's Defense by -1 CS. |
| 369 | `Hyperspace Hole` | Special | done | Bypasses interrupts and teleports between hits when possible. |
| 370 | `Hypnosis` | Status | done | Puts the target to Sleep. |
| 371 | `Ice Ball` | Physical | done | Consecutive uses scale DB by +3 up to DB 15 and reset on miss. |
| 372 | `Ice Beam` | Special | done | Freezes the target on 19+. |
| 373 | `Ice Burn` | Special | done | Implemented via explicit hook or generic handling. |
| 374 | `Ice Fang` | Physical | done | 18-19 inflicts Freeze or Flinch; 20 inflicts both. |
| 375 | `Ice Hammer` | Physical | done | Lowers the user's Speed by -1 CS. |
| 376 | `Ice Punch` | Physical | done | Freezes the target on 19+. |
| 377 | `Ice Shard` | Physical | done | Logs the priority strike. |
| 378 | `Icicle Crash` | Physical | done | Flinches on 15+. |
| 379 | `Icicle Spear` | Physical | done | Implemented via explicit hook or generic handling. |
| 380 | `Icy Wind` | Special | done | Lowers Speed by -1 CS on hit targets. |
| 381 | `Imprison` | Status | done | Implemented via explicit hook or generic handling. |
| 382 | `Incinerate` | Special | done | Drops a held item on hit and logs when none are found. |
| 383 | `Infernal Parade` | Special | done | Burns on 17+ and gains DB 12 once per scene vs afflicted targets. |
| 384 | `Inferno` | Special | done | Burns the target and can ignore evasion in open terrain. |
| 385 | `Infestation` | Special | done | Applies Vortex and Trapped for 3 rounds. |
| 386 | `Ingrain` | Status | done | Implemented via explicit hook or generic handling. |
| 387 | `Instruct` | Status | done | Implemented via explicit hook or generic handling. |
| 388 | `Intercept Melee` | Status | done | Implemented via explicit hook or generic handling. |
| 389 | `Intercept Ranged` | Status | done | Implemented via explicit hook or generic handling. |
| 390 | `Ion Deluge` | Status | done | Creates a short-lived ion zone that electrifies Normal moves. |
| 391 | `Iron Defense` | Status | done | Raises Defense by +2 CS. |
| 392 | `Iron Head` | Physical | done | Flinches on 15+. |
| 393 | `Iron Tail` | Physical | done | Implemented via explicit hook or generic handling. |
| 394 | `Jaw Lock` | Physical | done | Triggers a free Grapple contest on hit. |
| 395 | `Judgement` | Special | done | Implemented via explicit hook or generic handling. |
| 396 | `Jump Kick` | Physical | done | Miss recoil (1/4 max HP) unless blocked by shields; unusable under Gravity. |
| 397 | `Jungle Healing` | Status | done | Heals allies in burst for 1/4 max HP and cures persistent/volatile statuses. |
| 398 | `Karate Chop` | Physical | done | Critical hit threshold lowered to 17+. |
| 399 | `Kinesis` | Status | done | Applies a one-use interrupt that imposes a -4 accuracy penalty. |
| 400 | `King's Shield` | Status | done | Sets up a blocking interrupt that lowers Attack by -2 CS on melee hits. |
| 401 | `Knock Off` | Physical | done | Removes a held item from the target. |
| 402 | `Land's Wrath` | Physical | done | Logs Groundshaper grant (no extra mechanics yet). |
| 403 | `Laser Focus` | Status | done | Grants a guaranteed critical hit on the next damaging attack. |
| 404 | `Lash Out` | Physical | done | Boosts to DB 15 after losing CS, once per target per scene. |
| 405 | `Last Resort` | Physical | done | Requires five other distinct moves since the last switch. |
| 406 | `Lava Plume` | Special | done | Burns targets on 16+. |
| 407 | `Leaf Blade` | Physical | done | Critical hit threshold lowered to 18+. |
| 408 | `Leaf Storm` | Special | done | Implemented via explicit hook or generic handling. |
| 409 | `Leaf Tornado` | Special | done | Center small/medium targets are missed; 15+ lowers Accuracy by -1 CS. |
| 410 | `Leafage` | Physical | done | No special hook beyond baseline resolution. |
| 411 | `Leech Life` | Physical | done | Heals half the damage dealt. |
| 412 | `Leech Life [SM]` | Physical | done | Heals half the damage dealt. |
| 413 | `Leech Seed` | Status | done | Applies Leech Seed ticks for 1/10 max HP and heals the source. |
| 414 | `Leer` | Status | done | Lowers Defense by -1 CS on hit. |
| 415 | `Lick` | Physical | done | Paralyzes on 15+. |
| 416 | `Life Dew` | Status | done | Heals allies in burst for 1/4 max HP. |
| 417 | `Light of Ruin` | Special | done | Implemented via explicit hook or generic handling. |
| 418 | `Light Screen` | Status | done | Applies a Light Screen blessing with two charges. |
| 419 | `Liquidation` | Physical | done | Lowers Defense by -1 CS on 17+. |
| 420 | `Lock-On` | Status | done | Implemented via explicit hook or generic handling. |
| 421 | `Lovely Kiss` | Status | done | Puts the target to sleep. |
| 422 | `Low Blow` | Status | done | Opposed Acrobatics; on success inflicts Vulnerable and Bashed. |
| 423 | `Low Kick` | Physical | done | DB equals twice the target's Weight Class. |
| 424 | `Low Sweep` | Physical | done | Lowers Speed by -1 CS on hit. |
| 425 | `Lucky Chant` | Status | done | Applies a three-charge blessing that negates critical hits. |
| 426 | `Lunar Blessing` | Status | done | Heals 50% max HP, clears statuses, and grants an evasion bonus. |
| 427 | `Lunar Dance` | Status | done | User faints to restore target HP, heal injuries, and refresh move frequency. |
| 428 | `Lunge` | Physical | done | After sprint, applies -5 damage penalty to the target's next attack. |
| 429 | `Luster Purge` | Special | done | Even-numbered rolls lower Special Defense by -1 CS. |
| 430 | `Mach Punch` | Physical | done | Logs the priority strike. |
| 431 | `Magic Burst` | Special | done | Prevents attacks of opportunity for 1 round on hit foes. |
| 432 | `Magic Coat` | Status | done | Readies a status-reflecting interrupt that blocks non-damaging status moves. |
| 433 | `Magic Powder` | Status | done | Adds the Psychic type for 5 turns. |
| 434 | `Magic Room` | Status | done | Suppresses static item effects while active. |
| 435 | `Magical Leaf` | Special | done | Implemented via explicit hook or generic handling. |
| 436 | `Magma Storm` | Special | done | Applies Vortex and Trapped even on a miss. |
| 437 | `Magnet Bomb` | Physical | done | Implemented via explicit hook or generic handling. |
| 438 | `Magnet Rise` | Status | done | Grants levitation for 5 turns. |
| 439 | `Magnetic Flux` | Status | done | Raises Defense and Special Defense for Plus/Minus targets. |
| 440 | `Magnetic Flux [SM]` | Status | done | Raises Defense and Special Defense for Plus/Minus targets. |
| 441 | `Magnetic Flux [SS]` | Status | done | Adjusts Defense and Special Defense for Electric/Magnetic targets. |
| 442 | `Magnitude` | Physical | done | Rolls a d6 to set the damage base and logs the roll. |
| 443 | `Maneuver` | Category | done | Handled via trainer maneuver system. |
| 444 | `Manipulate` | Status | done | Triggers trainer social maneuvers based on the users best social skill. |
| 445 | `Mat Block` | Status | done | Round 1 shield that blocks an incoming attack for adjacent allies. |
| 446 | `Maul` | Physical | done | Flinches the target. |
| 447 | `Me First` | Status | done | Copies a faster foes declared damaging attack as an interrupt. |
| 448 | `Mean Look` | Status | done | Applies Trapped and Slowed for the encounter. |
| 449 | `Meditate` | Status | done | Raises the user's Attack by +1 CS. |
| 450 | `Mega Drain` | Special | done | Heals half the damage dealt. |
| 451 | `Mega Kick` | Physical | done | Implemented via explicit hook or generic handling. |
| 452 | `Mega Punch` | Physical | done | No special hook beyond baseline resolution. |
| 453 | `Megahorn` | Physical | done | Implemented via explicit hook or generic handling. |
| 454 | `Memento` | Status | done | Lowers all combat stages by -2 CS on the target. |
| 455 | `Metal Burst` | Physical | done | Implemented via explicit hook or generic handling. |
| 456 | `Metal Claw` | Physical | done | Raises Attack by +1 CS on 18+. |
| 457 | `Metal Sound` | Status | done | Lowers Special Defense by -2 CS on hit targets. |
| 458 | `Meteor Assault` | Physical | done | Implemented via explicit hook or generic handling. |
| 459 | `Meteor Beam` | Special | done | Implemented via explicit hook or generic handling. |
| 460 | `Meteor Mash` | Physical | done | Raises Attack by +1 CS on 15+. |
| 461 | `Metronome` | Status | done | Selects a random legal move to execute. |
| 462 | `MH Adept` | -- | done | Monster Hunter perk entry tracked externally. |
| 463 | `MH Expert` | -- | done | Monster Hunter perk entry tracked externally. |
| 464 | `Milk Drink` | Status | done | Restores 50% max HP to the target. |
| 465 | `Mimic` | Status | done | Implemented via explicit hook or generic handling. |
| 466 | `Mind Blown` | Special | done | Implemented via explicit hook or generic handling. |
| 467 | `Mind Reader` | Status | done | Marks a target for auto-hit or auto-miss through the next turn. |
| 468 | `Minimize` | Status | done | Grants evasion and shrinks the user. |
| 469 | `Miracle Eye` | Status | done | Psychic moves can hit Dark targets for the rest of the turn. |
| 470 | `Mirror Coat` | Status | done | Implemented via explicit hook or generic handling. |
| 471 | `Mirror Move` | Status | done | Implemented via explicit hook or generic handling. |
| 472 | `Mirror Shot` | Special | done | Lowers Accuracy by -2 on 16+. |
| 473 | `Mist` | Status | done | Applies a three-charge blessing that blocks combat stage drops. |
| 474 | `Mist Ball` | Special | done | Even-numbered rolls lower Special Attack by -1 CS. |
| 475 | `Misty Explosion` | Special | done | Implemented via explicit hook or generic handling. |
| 476 | `Misty Terrain` | Status | done | Sets Misty Terrain for 5 rounds, blocks status/confusion for grounded targets, and halves Dragon damage. |
| 477 | `Moonblast` | Special | done | Lowers Special Attack by -1 CS on 15+. |
| 478 | `Moongeist Beam` | Special | done | Ignores defensive abilities. |
| 479 | `Moonlight` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 480 | `Morning Sun` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 481 | `Mountain Gale` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 482 | `Mud Bomb` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 483 | `Mud Shot` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 484 | `Mud Sport` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 485 | `Mud-Slap` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 486 | `Muddy Water` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 487 | `Multi-Attack` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 488 | `Multi-Attack [SS]` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 489 | `Mystical Fire` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 490 | `Mystical Power` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 491 | `Name` | Category | pending | Hook pending; covered only by baseline attack pipeline. |
| 492 | `Nasty Plot` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 493 | `Natural Gift` | Special | done | Bespoke move hook supported by autonomous engine. |
| 494 | `Nature Power` | Status | done | Bespoke move hook supported by autonomous engine. |
| 495 | `Nature's Madness` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 496 | `Nature’s Madness` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 497 | `Needle Arm` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 498 | `Night Daze` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 499 | `Night Shade` | Special | done | Bespoke move hook supported by autonomous engine. |
| 500 | `Night Slash` | Physical | done | Bespoke move hook + Critical hit on accuracy rolls of 18+ supported by autonomous engine. |
| 501 | `Nightmare` | Status | done | Bespoke move hook + Applies Bad Sleep to sleeping targets supported by autonomous engine. |
| 502 | `No Retreat` | Status | done | Raises all stats by +1 CS and prevents switching out supported by autonomous engine. |
| 503 | `Noble Roar` | Status | done | Lowers Attack and Special Attack by -1 CS on hit supported by autonomous engine. |
| 504 | `Nuzzle` | Physical | done | Paralyzes the target on hit supported by autonomous engine. |
| 505 | `Oblivion Wing` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 506 | `Obstruct` | Status | done | Bespoke move hook supported by autonomous engine. |
| 507 | `Octazooka` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 508 | `Octolock` | Status | done | Bespoke move hook supported by autonomous engine. |
| 509 | `Odor Sleuth` | Status | done | Bespoke move hook supported by autonomous engine. |
| 510 | `OH Adept` | -- | done | Placeholder move entry has no combat effect in the engine data. |
| 511 | `Ominous Wind` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 512 | `Origin Pulse` | Special | done | Implemented via explicit hook or generic handling. |
| 513 | `Outrage` | Physical | done | Implemented via explicit hook or generic handling. |
| 514 | `Overdrive` | Special | done | No bespoke effect beyond baseline damage. |
| 515 | `Overheat` | Special | done | Implemented via explicit hook or generic handling. |
| 516 | `Pain Split` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 517 | `Parabolic Charge` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 518 | `Parabolic Charge [SM]` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 519 | `Parting Shot` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 520 | `Pay Day` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 521 | `Payback` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 522 | `Peck` | Physical | done | No bespoke effect beyond baseline damage. |
| 523 | `Perish Song` | Status | done | Implemented via explicit hook or generic handling. |
| 524 | `Petal Blizzard` | Physical | done | No bespoke effect beyond baseline damage. |
| 525 | `Petal Dance` | Special | done | Implemented via explicit hook or generic handling. |
| 526 | `Phantom Force` | Physical | done | Implemented via explicit hook or generic handling. |
| 527 | `Photon Geyser` | Special | done | Bespoke move hook supported by autonomous engine. |
| 528 | `Pierce!` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 529 | `Pin Missile` | Physical | done | Implemented via explicit hook or generic handling. |
| 530 | `Plasma Fists` | Physical | done | Implemented via explicit hook or generic handling. |
| 531 | `Play Nice` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 532 | `Play Rough` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 533 | `Pluck` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 534 | `Poison Fang` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 535 | `Poison Gas` | Status | done | Bespoke move hook supported by autonomous engine. |
| 536 | `Poison Jab` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 537 | `Poison Powder` | Status | done | Bespoke move hook supported by autonomous engine. |
| 538 | `Poison Sting` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 539 | `Poison Tail` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 540 | `Pollen Puff` | Special | done | Bespoke move hook supported by autonomous engine. |
| 541 | `Poltergeist` | Physical | done | Implemented via explicit hook or generic handling. |
| 542 | `Pound` | Physical | done | No bespoke effect beyond baseline damage. |
| 543 | `Powder` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 544 | `Powder Snow` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 545 | `Power Gem` | Special | done | No bespoke effect beyond baseline damage. |
| 546 | `Power Shift` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 547 | `Power Split` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 548 | `Power Swap` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 549 | `Power Trick` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 550 | `Power Trip` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 551 | `Power Whip` | Physical | done | Implemented via explicit hook or generic handling. |
| 552 | `Power-Up Punch` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 553 | `Precipice Blades` | Physical | done | Implemented via explicit hook or generic handling. |
| 554 | `Present` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 555 | `Prismatic Laser` | Special | done | Implemented via explicit hook or generic handling. |
| 556 | `Protect` | Status | done | Bespoke move hook supported by autonomous engine. |
| 557 | `Psybeam` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 558 | `Psych Up` | Status | done | Implemented via explicit hook or generic handling. |
| 559 | `Psychic` | Special | done | Implemented via explicit hook or generic handling. |
| 560 | `Psychic Fangs` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 561 | `Psychic Terrain` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 562 | `Psycho Boost` | Special | done | Implemented via explicit hook or generic handling. |
| 563 | `Psycho Cut` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 564 | `Psycho Shift` | Status | done | Implemented via explicit hook or generic handling. |
| 565 | `Psyshield Bash` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 566 | `Psyshock` | Special | done | Bespoke move hook supported by autonomous engine. |
| 567 | `Psystrike` | Special | done | Bespoke move hook supported by autonomous engine. |
| 568 | `Psywave` | Special | done | Bespoke move hook supported by autonomous engine. |
| 569 | `Punishment` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 570 | `Purify` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 571 | `Pursuit` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 572 | `Push` | Status | done | Implemented via explicit hook or generic handling. |
| 573 | `Pyro Ball` | Physical | done | Implemented via explicit hook or generic handling. |
| 574 | `Quash` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 575 | `Quick Attack` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 576 | `Quick Guard` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 577 | `Quiver Dance` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 578 | `Rage` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 579 | `Rage Powder` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 580 | `Raging Fury` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 581 | `Rain Dance` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 582 | `Rapid Spin` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 583 | `Rapid Spin [SS]` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 584 | `Razor Leaf` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 585 | `Razor Shell` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 586 | `Razor Wind` | Special | done | Implemented via explicit hook or generic handling. |
| 587 | `Recover` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 588 | `Recycle` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 589 | `Reflect` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 590 | `Reflect Type` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 591 | `Refresh` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 592 | `Relic Song` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 593 | `Rending Spell` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 594 | `Resonance Beam` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 595 | `Rest` | Status | done | Bespoke move hook supported by autonomous engine. |
| 596 | `Retaliate` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 597 | `Return` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 598 | `Revelation Dance` | Special | done | Bespoke move hook supported by autonomous engine. |
| 599 | `Revenge` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 600 | `Reversal` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 601 | `Riposte` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 602 | `Rising Voltage` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 603 | `Roar` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 604 | `Roar of Time` | Special | done | Implemented via explicit hook or generic handling. |
| 605 | `Rock Blast` | Physical | done | Implemented via explicit hook or generic handling. |
| 606 | `Rock Climb` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 607 | `Rock Polish` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 608 | `Rock Slide` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 609 | `Rock Smash` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 610 | `Rock Throw` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 611 | `Rock Tomb` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 612 | `Rock Wrecker` | Physical | done | Implemented via explicit hook or generic handling. |
| 613 | `Role Play` | Status | done | Implemented via explicit hook or generic handling. |
| 614 | `Rolling Kick` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 615 | `Rollout` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 616 | `Roost` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 617 | `Rototiller` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 618 | `Round` | Special | done | Bespoke move hook supported by autonomous engine. |
| 619 | `Sacred Fire` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 620 | `Sacred Sword` | Physical | done | Implemented via explicit hook or generic handling. |
| 621 | `Safeguard` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 622 | `Salvo` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 623 | `Sand Attack` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 624 | `Sand Tomb` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 625 | `Sandstorm` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 626 | `Sandstorm Sear` | Special | done | Implemented via explicit hook or generic handling. |
| 627 | `Scald` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 628 | `Scale Shot` | Physical | done | Implemented via explicit hook or generic handling. |
| 629 | `Scary Face` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 630 | `Scorching Sands` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 631 | `Scratch` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 632 | `Screech` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 633 | `Searing Shot` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 634 | `Secret Force` | Special | done | Implemented via explicit hook or generic handling. |
| 635 | `Secret Power` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 636 | `Secret Sword` | Special | done | Bespoke move hook supported by autonomous engine. |
| 637 | `Seed Bomb` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 638 | `Seed Flare` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 639 | `Seismic Toss` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 640 | `Self-Destruct` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 641 | `Shadow Ball` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 642 | `Shadow Bone` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 643 | `Shadow Claw` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 644 | `Shadow Force` | Physical | done | Implemented via explicit hook or generic handling. |
| 645 | `Shadow Punch` | Physical | done | Implemented via explicit hook or generic handling. |
| 646 | `Shadow Sneak` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 647 | `Sharpen` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 648 | `Sheer Cold` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 649 | `Shell Side Arm` | Special | done | Bespoke move hook supported by autonomous engine. |
| 650 | `Shell Smash` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 651 | `Shell Trap` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 652 | `Shelter` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 653 | `Shift Gear` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 654 | `Shock Wave` | Special | done | Implemented via explicit hook or generic handling. |
| 655 | `Shore Up` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 656 | `Signal Beam` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 657 | `Silver Wind` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 658 | `Simple Beam` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 659 | `Sing` | Status | done | Bespoke move hook supported by autonomous engine. |
| 660 | `Sketch` | Status | done | Implemented via explicit hook or generic handling. |
| 661 | `Skill Swap` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 662 | `Skitter Smack` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 663 | `Skull Bash` | Physical | done | Implemented via explicit hook or generic handling. |
| 664 | `Sky Attack` | Physical | done | Implemented via explicit hook or generic handling. |
| 665 | `Sky Drop` | Physical | done | Implemented via explicit hook or generic handling. |
| 666 | `Sky Uppercut` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 667 | `Slack Off` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 668 | `Slam` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 669 | `Slash` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 670 | `Sleep Powder` | Status | done | Bespoke move hook supported by autonomous engine. |
| 671 | `Sleep Talk` | Status | done | Bespoke move hook supported by autonomous engine. |
| 672 | `Slice` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 673 | `Sludge` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 674 | `Sludge Bomb` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 675 | `Sludge Wave` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 676 | `Smack Down` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 677 | `Smart Strike` | Physical | done | Implemented via explicit hook or generic handling. |
| 678 | `Smelling Salts` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 679 | `Smog` | Special | done | Bespoke move hook supported by autonomous engine. |
| 680 | `Smokescreen` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 681 | `Snap Trap` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 682 | `Snarl` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 683 | `Snatch` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 684 | `Snipe Shot` | Special | done | Bespoke move hook supported by autonomous engine. |
| 685 | `Snore` | Special | done | Bespoke move hook supported by autonomous engine. |
| 686 | `Soak` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 687 | `Soft-Boiled` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 688 | `Solar Beam` | Special | done | Implemented via explicit hook or generic handling. |
| 689 | `Solar Blade` | Physical | done | Implemented via explicit hook or generic handling. |
| 690 | `Sonic Boom` | Special | done | Bespoke move hook supported by autonomous engine. |
| 691 | `Spacial Rend` | Special | done | Bespoke move hook supported by autonomous engine. |
| 692 | `Spark` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 693 | `Sparkling Aria` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 694 | `Spectral Thief` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 695 | `Speed Swap` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 696 | `Spider Web` | Status | done | Implemented via explicit hook or generic handling. |
| 697 | `Spike Cannon` | Physical | done | Implemented via explicit hook or generic handling. |
| 698 | `Spikes` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 699 | `Spiky Shield` | Status | done | Bespoke move hook supported by autonomous engine. |
| 700 | `Spirit Break` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 701 | `Spirit Lance` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 702 | `Spirit Shackle` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 703 | `Spit Up` | Special | done | Bespoke move hook supported by autonomous engine. |
| 704 | `Spite` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 705 | `Splash` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 706 | `Spore` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 707 | `Spotlight` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 708 | `Springtide Storm` | Special | done | Implemented via explicit hook or generic handling. |
| 709 | `Sprint` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 710 | `Stealth Rock` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 711 | `Steam Eruption` | Special | done | Implemented via explicit hook or generic handling. |
| 712 | `Steamroller` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 713 | `Steel Beam` | Special | done | Implemented via explicit hook or generic handling. |
| 714 | `Steel Roller` | Physical | done | Implemented via explicit hook or generic handling. |
| 715 | `Steel Wing` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 716 | `Sticky Web` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 717 | `Stockpile` | Status | done | Bespoke move hook supported by autonomous engine. |
| 718 | `Stomp` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 719 | `Stomping Tantrum` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 720 | `Stone Axe` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 721 | `Stone Edge` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 722 | `Stored Power` | Special | done | Bespoke move hook supported by autonomous engine. |
| 723 | `Storm Throw` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 724 | `Strange Steam` | Special | done | Bespoke move hook supported by autonomous engine. |
| 725 | `Strength` | Physical | done | Implemented via explicit hook or generic handling. |
| 726 | `Strength Sap` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 727 | `String Shot` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 728 | `Struggle` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 729 | `Struggle Bug` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 730 | `Struggle+` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 731 | `Stuff Cheeks` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 732 | `Stun Spore` | Status | done | Bespoke move hook supported by autonomous engine. |
| 733 | `Submission` | Physical | done | Implemented via explicit hook or generic handling. |
| 734 | `Substitute` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 735 | `Sucker Punch` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 736 | `Sucker Punch [SM]` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 737 | `Sunny Day` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 738 | `Sunsteel Strike` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 739 | `Super Fang` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 740 | `Superpower` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 741 | `Supersonic` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 742 | `Surf` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 743 | `Surging Strikes` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 744 | `Swagger` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 745 | `Swagger [SM]` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 746 | `Swallow` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 747 | `Sweeping Strike` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 748 | `Sweet Kiss` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 749 | `Sweet Scent` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 750 | `Swift` | Special | done | Implemented via explicit hook or generic handling. |
| 751 | `Switcheroo` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 752 | `Swords Dance` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 753 | `Synchronoise` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 754 | `Synthesis` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 755 | `Tackle` | Physical | done | Implemented via explicit hook or generic handling. |
| 756 | `Tackle [SM]` | Physical | done | Implemented via explicit hook or generic handling. |
| 757 | `Tail Glow` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 758 | `Tail Slap` | Physical | done | Implemented via explicit hook or generic handling. |
| 759 | `Tail Whip` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 760 | `Tailwind` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 761 | `Take Aim` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 762 | `Take Down` | Physical | done | Implemented via explicit hook or generic handling. |
| 763 | `Take Heart` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 764 | `Tar Shot` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 765 | `Taunt` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 766 | `Tearful Look` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 767 | `Teatime` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 768 | `Techno Blast` | Special | done | Bespoke move hook supported by autonomous engine. |
| 769 | `Teeter Dance` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 770 | `Telekinesis` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 771 | `Teleport` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 772 | `Terrain Pulse` | Special | done | Bespoke move hook supported by autonomous engine. |
| 773 | `Terrorize` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 774 | `Thief` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 775 | `Thousand Arrows` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 776 | `Thousand Waves` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 777 | `Thrash` | Physical | done | Implemented via explicit hook or generic handling. |
| 778 | `Throat Chop` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 779 | `Thunder` | Special | done | Implemented via explicit hook or generic handling. |
| 780 | `Thunder Cage` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 781 | `Thunder Fang` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 782 | `Thunder Punch` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 783 | `Thunder Shock` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 784 | `Thunder Wave` | Status | done | Implemented via explicit hook or generic handling. |
| 785 | `Thunder Wave [SM]` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 786 | `Thunderbolt` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 787 | `Thunderous Kick` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 788 | `Tickle` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 789 | `Titanic Slam` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 790 | `Topsy-Turvy` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 791 | `Torment` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 792 | `Toxic` | Status | done | Implemented via explicit hook or generic handling. |
| 793 | `Toxic Spikes` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 794 | `Toxic Thread` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 795 | `Toxic Threads` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 796 | `Transform` | Status | done | Implemented via explicit hook or generic handling. |
| 797 | `Tri Attack` | Special | done | Bespoke move hook supported by autonomous engine. |
| 798 | `Trick` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 799 | `Trick Room` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 800 | `Trick-or-Treat` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 801 | `Trip` | Status | done | Bespoke move hook supported by autonomous engine. |
| 802 | `Triple Arrows` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 803 | `Triple Axel` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 804 | `Triple Kick` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 805 | `Triple Kick [LA]` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 806 | `Triple Threat` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 807 | `Trop Kick` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 808 | `Trump Card` | Special | done | Bespoke move hook supported by autonomous engine. |
| 809 | `Twineedle` | Physical | done | Implemented via explicit hook or generic handling. |
| 810 | `Twister` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 811 | `U-Turn` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 812 | `Uproar` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 813 | `V-Create` | Physical | done | Implemented via explicit hook or generic handling. |
| 814 | `Vacuum Wave` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 815 | `Venom Drench` | Status | done | Implemented via explicit hook or generic handling. |
| 816 | `Venoshock` | Special | done | Bespoke move hook supported by autonomous engine. |
| 817 | `Vicegrip` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 818 | `Victory Dance` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 819 | `Vine Whip` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 820 | `Vital Throw` | Physical | done | Implemented via explicit hook or generic handling. |
| 821 | `Volt Switch` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 822 | `Volt Tackle` | Physical | done | Implemented via explicit hook or generic handling. |
| 823 | `Wake-Up Slap` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 824 | `Water Gun` | Special | done | Bespoke move hook supported by autonomous engine. |
| 825 | `Water Pledge` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 826 | `Water Pulse` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 827 | `Water Shuriken` | Physical | done | Implemented via explicit hook or generic handling. |
| 828 | `Water Shuriken [SM]` | Special | done | Implemented via explicit hook or generic handling. |
| 829 | `Water Sport` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 830 | `Water Spout` | Special | done | Bespoke move hook supported by autonomous engine. |
| 831 | `Waterfall` | Physical | done | Bespoke move hook supported by autonomous engine. |
| 832 | `Wave Crash` | Physical | done | Implemented via explicit hook or generic handling. |
| 833 | `Wear Down` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 834 | `Weather Ball` | Special | done | Bespoke move hook supported by autonomous engine. |
| 835 | `Whirlpool` | Special | pending | Hook pending; covered only by baseline attack pipeline. |
| 836 | `Whirlwind` | Status | done | Implemented via explicit hook or generic handling. |
| 837 | `Wicked Blow` | Physical | done | Implemented via explicit hook or generic handling. |
| 838 | `Wide Guard` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 839 | `Wild Charge` | Physical | done | Implemented via explicit hook or generic handling. |
| 840 | `Wildbolt Storm` | Special | done | Implemented via explicit hook or generic handling. |
| 841 | `Will-O-Wisp` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 842 | `Wing Attack` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 843 | `Wish` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 844 | `Withdraw` | Status | done | Bespoke move hook supported by autonomous engine. |
| 845 | `Wonder Room` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 846 | `Wood Hammer` | Physical | done | Implemented via explicit hook or generic handling. |
| 847 | `Work Up` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 848 | `Worry Seed` | Status | pending | Hook pending; covered only by baseline attack pipeline. |
| 849 | `Wounding Strike` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 850 | `Wrap` | Static | pending | Hook pending; covered only by baseline attack pipeline. |
| 851 | `Wring Out` | Special | done | Bespoke move hook supported by autonomous engine. |
| 852 | `X-Scissor` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 853 | `Yawn` | Status | done | Implemented via explicit hook or generic handling. |
| 854 | `Zap Cannon` | Special | done | Bespoke move hook supported by autonomous engine. |
| 855 | `Zen Headbutt` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
| 856 | `Zing Zap` | Physical | pending | Hook pending; covered only by baseline attack pipeline. |
