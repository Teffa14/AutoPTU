# Implementation Status

This document enumerates what is **fully implemented** in AutoPTU as of generation time.
"Fully implemented" here means: a behavior has explicit code hooks and a corresponding test reference.

## Abilities (Implemented + Tested)
- `Abominable`
  Effect: The user ignores the Recoil Keyword when attacking, and does not gain injuries from Massive Damage.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Absorb Force`
  Effect: The user takes damage as if the attack was one step less effective.
Trigger - The user is damaged by a Physical Attack
  Code: `auto_ptu\rules\hooks\abilities\absorb_force_filter.py` -> `_absorb_force_reduce_effectiveness` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\absorb_force_filter.py`
- `Adaptability`
  Effect: Increase the Damage of all Moves with which the user shares an Elemental Type by +1 Damage Base.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`
- `Aerilate`
  Effect: The Move is Changed to Flying Type.
Trigger - The User uses a Normal Type Damaging Move.
  References: `auto_ptu\rules\battle_state.py`
- `Aftermath`
  Effect: When the user is reduced to 0 HP or less, they create a Burst 1. Everything in the Burst loses  of its Max Hit Points.
  References: `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Air Lock`
  Effect: The weather is set to Normal as long as the Pokmon with Air Lock wants it to remain that way. The user may continue to sustain this effect as a Swift Action each round.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\controllers\phase_controller.py`
- `Ambush`
  Effect: The user may use a Melee Move with a Damage Base of 6 (before applying STAB or other modifiers) or lower as if it had the Priority keyword. If it hits, the target is Flinched.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Analytic`
  Effect: Whenever the user targets uses a damaging Move on a Pokmon or Trainer that have acted before it during Initiative this Round, that Move deals an additional +5 Damage.
  Code: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py` -> `_analytic_bonus` (phase `post_result`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`
- `Anger Point`
  Effect: When the Pokmon receives a Critical Hit, they become Enraged and gain +6 Attack Combat Stages.
  References: `auto_ptu\rules\battle_state.py`
- `Anticipation`
  Effect: The target reveals if they have any Moves that are Super-Effective against the Pokmon with Anticipation. You may not target a Pokmon or Trainer more than once per encounter with Anticipation. Anticipation only reveals whether the opponent does or does not have those moves, not the specific moves themselves.
Target - Pokmon or Trainers
  References: `auto_ptu\rules\battle_state.py`
- `Aqua Boost`
  Effect: The allied target gains a +5 Bonus to its damage roll with the triggering Move.  A target may not benefit from more than one instance of Aqua Boost at a time.
Trigger - An adjacent Ally uses a Water-Type Move
  References: `auto_ptu\rules\hooks\abilities\aura_adjacent_bonuses.py`
- `Arena Trap`
  Effect: Once Arena trap is activated, all foes within 5 meters of the user are considered Slowed. This does not affect targets of the Flying Type, or with a Levitate, Sky, or Burrow Speed of 4 or higher. The user may end the effect as a Free Action, and the effect ends if the user is fainted or returned to a Pok Ball.
Target - Pokmon or Trainers
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Aroma Veil`
  Effect: The user and all Pokmon and Trainers within 3 meters cannot be Confused, Enraged, or Suppressed. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Aura Break`
  Effect: Foes may not benefit from Abilities that increase the Combat Stages or damage dealt by themselvs or their allies.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Aura Storm`
  Effect: For each injury the user has, they gain a +3 Damage bonus to all Moves with the Aura keyword. Additionally, while the user is at or under  of their Max Hit Points, they gain a +3 Damage Bonus to all Moves with the Aura Keyword.
  References: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`, `auto_ptu\rules\hooks\abilities\aura_adjacent_bonuses.py`
- `Bad Dreams`
  Effect: At the beginning of the user's turn, all Sleeping Pokmon or Trainers in a Burst 5 lose a Tick of Hit Points.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Battle Armor`
  Effect: The user is immune to Critical Hits; they are instead normal hits. Defensive.
  References: `auto_ptu\rules\abilities\damage_effects.py`
- `Beam Cannon`
  Effect: The Effect Range and Critical Hit Range of the user's Ranged, 1-Target Moves are increased by 3.
  References: `auto_ptu\rules\battle_state.py`
- `Beautiful`
  Effect: The user may activate Beautiful to either grain +2 Beauty DIce in a Contest, or to cure any adjacent targets of the Enraged Condition.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Berry Storage`
  Effect: The user gains 3 instances of the Berry's Digestion/Food Buff instead of 1. It may only trade in one of these Digestion/Food Buffs each Scene. Neither storing nor trading in these Digestion/Food Buffs counts against the user's normal limits. All Digestion/Food Buffs gained from Berry Storage are lost after an Extended Rest.
Trigger - The user eats a Berry
  References: `auto_ptu\rules\battle_state.py`
- `Big Pecks`
  Effect: The user cannot have its Defense Stat lowered. The user cannot have its Defense Combat Stages lowered. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Big Swallow`
  Effect: Connection - Stockpile. Whenever the user uses Swallow or Spit Up, it may treat the Stockpile Count as if it was one higher. This Ability has no effect if the Stockpile Counter is already 3.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Blaze`
  Effect: The user gains Last Chance with Fire.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Blessed Touch`
  Effect: An adjacent Pokmon or Trainer gains Hit Points equal to 1/4th of its maximum Hit Points.
  References: `auto_ptu\rules\abilities\ability_moves.py`
- `Blow Away`
  Effect: Connection - Whirlwind. When the user uses Whirlwind, all targets hit lose a Tick of Hit Points.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Blur`
  Effect: Attacks and Moves targeting you that don't require an Accuracy Check now require one, as though they had an Accuracy Check of 2. You may only apply half of your Evasion to these Attacks and Moves. Defensive.
  References: `auto_ptu\rules\calculations.py`
- `Bodyguard`
  Effect: The user and the target switch places, and the user becomes the target of the attack instead, taking damage from the attack as if resisted one step further. If switching places would not move the triggering Ally out of the area-of-effect of a Burst, Blast, Cone, or Line, this Ability does not prevent the ally from being hit. Defensive.
Trigger - A cardinally adjacent Ally is hit by an attack
  References: `auto_ptu\rules\battle_state.py`
- `Bone Lord`
  Effect: Connection - Bonemerang. This Ability may be activated when hitting with Bone Club to automatically Flinch its target; or to use Bonemerang as a Priority Move; or when hitting with Bone Rush to cause the attack to automatically hit 5 times.
Trigger - The user hits with Bone Club, Bonemerang, or Bone Rush
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Bone Wielder`
  Effect: This ability is only functional if the user is holding a Thick Club item. The user gains a +1 Accuracy Bonus to Bone Club, Bonemerang, and Bone Rush. Additionally, the user cannot be disarmed, or have their Thick Club forcefully removed by Trick, Switcheroo, Thief, or any other Moves or effects unless the user wishes it.
  References: `auto_ptu\rules\calculations.py`
- `Brimstone`
  Effect: Whenever the user causes a Burn with a damaging Fire-Type Attack, the target is also Poisoned.
  References: `auto_ptu\rules\battle_state.py`
- `Bulletproof`
  Effect: The user resists all X target ranged attacks one step further. This refers to attacks and Moves that simply hit one target or specify hitting multiple targets, such as Razor Wind hitting three targets. It has no effect on Moves that are capable of hitting multiple targets through areas of effect, such as Bursts or Cones. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_bulletproof_resists_ranged` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Bully`
  Effect: The target of the attack  is pushed 2 Meters, becomes Tripped, and gains an Injury.
Trigger - The user hits the target for Super-Effective Damage with a Melee Move.
  Code: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py` -> `_bully_trips_on_super_effective_melee` (phase `post_result_bully`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`
- `Cave Crasher`
  Effect: The user resists Ground-Type and Rock-Type attacks one step further. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_cave_crasher_resists_ground` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Celebrate`
  Effect: The user increases their Speed by 1 Combat Stage and may immediately take an additional Shift Action to move as if they were Slowed. This Ability may only be activated if the user is not prevented from shifting.
Trigger - The user causes a foe to Faint by using a damaging attack
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Cherry Power`
  Effect: The user gains 15 Temporary Hit Points, and is cured of all Persistent Status Afflictions.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Chlorophyll`
  Effect: While in Sunny Weather, the user gains +4 Speed Combat Stages.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Clay Cannons`
  Effect: Until the end of the round, the user may originate any Ranged Move they use from any square adjacent to itself.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Clear Body`
  Effect: The user's Combat Stages may not be lowered by the effect of foes' Features, Abilities, or Moves. Status Affictions may still alter their Combat Stages. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Cloud Nine`
  Effect: The weather of the Field is set to Normal.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Cluster Mind`
  Effect: The user's Move Pool limit is increased by +2.
  References: `auto_ptu\rules\abilities\ability_moves.py`
- `Color Change`
  Effect: The User's Type changes to match the Type of the triggering Move.
Trigger - The user is hit by a Move
  References: `auto_ptu\rules\battle_state.py`
- `Color Theory`
  Effect: Upon gaining this ability at Birth, the user rolls 1d12 to determine the color of their tail secretions. 1 = Red; 2 = Red-Orange; 3 = Orange; 4 = Yellow- Orange; 5 = Yellow; 6 = Yellow-Green; 7 = Green; 8 = Blue-Green; 9 = Blue; 10 = Blue-Violet; 11 = Violet; 12 = Red-Violet.
Red is tied to Attack, Orange is tied to Defense, Yellow is tied to Special Attack, Green is tied to Special Defense, Blue is tied to Speed, Violet is tied to HP. Users with a "Pure" Color (Red, Orange, Yellow, etc) gain a +6 Bonus to the Base Stat tied to their color. Users with a "Mixed" Color (Red-Orange, Yellow-Orange, etc) gain a +3 Bonus to each Stat tied to the color.
  References: `auto_ptu\rules\abilities\ability_moves.py`
- `Competitive`
  Effect: Whenever the user has its Combat Stages lowered, by something other than its own Moves or Abilities, the user's Special Attack is raised 2 Combat Stages.
  References: `auto_ptu\rules\hooks\abilities\combat_stage_reactions.py`
- `Compound Eyes`
  Effect: The user gains a +3 Bonus to all Accuracy Rolls.
  References: `auto_ptu\rules\calculations.py`
- `Confidence`
  Effect: Choose a Combat Stat. All allies within 5 meters of the user gain +1 CS in the Chosen Stat.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Conqueror`
  Effect: The user's Attack, Special Attack, and Speed gain +1 Combat Stage.
Trigger - The user causes a foe to Faint by using a damaging Physical or Special Attack
  References: `auto_ptu\rules\battle_state.py`
- `Contrary`
  Effect: If something would raise the user's Combat Stages, it instead lowers the user's Combat Stages by the same amount. If something would lower the user's Combat Stages, it instead raises the user's Combat Stages by the same amount.
  References: `auto_ptu\rules\battle_state.py`
- `Copy Master`
  Effect: Connection - Copycat. Whenever the user uses Copycat or Mimic, it gains +1 Combat Stage in a Stat of its choIce after the Move is resolved.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Corrosive Toxins`
  Effect: Connection - Toxic. The user may activate this Ability when using Toxic to allow the Move to ignore Immunity to the Status Affliction, Blessings, and the effects of Abilities that may prevent Hit Point loss from being Badly Poisoned (such as Magic Guard or Poison Heal).
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\controllers\phase_controller.py`
- `Courage`
  Effect: While at or under 1/3rd of its Max Hit Point value, the user gains a +5 Damage Bonus to all Damage Rolls, and 5 Damage Reduction. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_courage_reduces_damage_at_low_hp` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Covert`
  Effect: If this Pokmon is standing on a terrain related to its natural habitat, its Evasion is increased by +2. For Ice types, this is generally snowy or icy terrain; Ground and Ground types are apt to feel at home in sandy terrain or craggy rocks; Grass types, Bug Types, and others likely feel at home in long grass. Some Pokmon may be at home in several types of terrain.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Cruelty`
  Effect: After Damage is Resolved, the foe gains an Injury. The user is then informed of the total number of Injuries currently on the target, and may use that number to "purchase" the effects listed below.
1 Injury: The target loses 2 Hit Points. May be "purchased" multiple times.
1 Injury: The target is Slowed.
2 Injuries: Until the end of the encounter, the target may not gain Hit Points or Temporary Hit Points from any source. This effect ends if the target is switched out or Takes a Breather.
Trigger - The user hits a foe with a damaging attack
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_cruelty_adds_injury` (phase `post_damage_followup`, holder `attacker`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`
- `Crush Trap`
  Effect: Connection - Wrap. When you activate this ability, the user may immediately deal damage to the target as if the user had hit with a Struggle Attack. There is no Accuracy Roll and thus this damage cannot miss, be a Critical Hit, or trigger any Effect Ranges.
Trigger - The user successfully grapples a target.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Cursed Body`
  Effect: The Move becomes Disabled.
Trigger - The user is hit by a Damaging Move.
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Cute Charm`
  Effect: The foe becomes Infatuated.
Trigger - A foe of the opposite gender attacks the user with a Melee Attack
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Cute Tears`
  Effect: The attacking foe loses 2 Combat Stages in the Attack Stat used by the triggering Move.
Trigger - The user is hit by a Damaging Move.
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Damp`
  Effect: The Moves Self-Destruct and Explosion may not be used when a Pokmon with Damp is within 10-meters of Self-Destruct or Explosion's user. The Ability Aftermath may not be activated when a Pokmon with Damp is within 10-meters of the Pokmon attempting to activate Aftermath.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Danger Syrup`
  Effect: Connection - Sweet Scent.  If the user it hit by a damaging attack, it may use Sweet Scent as a Free action, frequency allowing.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\contact_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Dark Art`
  Effect: The user gains Last Chance with Dark.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Dark Aura`
  Effect: The user and all allies have the Damage Base of their damaging Dark Type Attacks increased by +1.
  References: `auto_ptu\rules\battle_state.py`
- `Daze`
  Effect: Make an AC4 Status attack against a target within 6 meters.  If you hit, the target falls Asleep.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Deadly Poison`
  Effect: The target is Badly Poisoned instead.
Trigger - The user Poisons a target
  References: `auto_ptu\rules\battle_state.py`
- `Decoy`
  Effect: The user uses the Move "Follow Me" as if it was on their Move List, and their Evasion is raised by +2 until the end of their next turn.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Deep Sleep`
  Effect: When asleep, this Pokmon restores a Tick of Hit Points at the end of each turn.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Defeatist`
  Effect: Whenever the user is brought below 50% of their max Hit Points, the user's Attack and Special Attack are lowered by 1 Combat Stage each, and the user's Speed is increased by +2 Combat Stages. If the user is healed above 50% max Hit Points, these changes are reverted.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Defiant`
  Effect: Whenever the user has its Combat Stages lowered, by something other than its own Moves or Abilities, the user's Attack is raised 2 Combat Stages.
  References: `auto_ptu\rules\hooks\abilities\combat_stage_reactions.py`
- `Defy Death`
  Effect: By activating this Ability, the user is instantly healed of up to 2 Injuries;  These count towards the total number of Injuries that can be healed each day.  Additionally, to die, the user must reach -250% Hit Points instead of -200% Hit Points.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Delayed Reaction`
  Effect: Halve the damage taken by the user. At the end of the user's next turn, the user loses Hit Points equal to the other half of the damage. For example, if the user is hit for 11 damage and triggers this Ability, the user would take 5 damage upon being hit and 6 damage at the end of its next turn. Defensive.
Trigger - The user is hit by a direct damaging attack
  Code: `auto_ptu\rules\hooks\abilities\pre_apply_damage.py` -> `_delayed_reaction_stores_damage` (phase `pre_apply_damage`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\abilities\pre_apply_damage.py`
- `Delivery Bird`
  Effect: The user may hold two Held Items at once. Whenever an Ability or Move affects the user's Held Items, you may choose which one is affected.
  References: `auto_ptu\rules\battle_state.py`
- `Desert Weather`
  Effect: The user is immune to Sandstorm Damage, resists Fire-Type Moves in Sunny Weather, and regains 1/16th of its Max Hit Points at the end of each of its turns while in Rainy Weather.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\abilities\pre_apply_damage.py`
- `Diamond Defense`
  Effect: Connection - Stealth Rock. Stealth Rock's Frequency is Scene x2, and the user's Stealth Rocks can be treated as dealing Rock-Type or Fairy-Type Damage, whichever is more effective.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Dig Away`
  Effect: Connection - Dig. When hit by a Move, this Pokmon may activate this Feature to use Dig, frequency allowing, as an interrupt to avoid the attack and shift underground immediately. This consumes a command as normal. The terrain must allow for Dig to be used.
  References: `auto_ptu\rules\battle_state.py`
- `Dire Spore`
  Effect: Connection - Spore. Whenever the user hits a target with Spore, that target is also Poisoned.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Discipline`
  Effect: If the user gains initiative and is Confused, Enraged, Infatuated, or Flinched, they may activate Discipline to cure themselves of any of these conditions.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Disguise`
  References: `auto_ptu\rules\hooks\abilities\pre_apply_damage.py`
- `Dodge`
  Effect: The triggering Move instead misses. Defensive.
Trigger - The user is hit by a Damaging Move.
  References: `auto_ptu\rules\abilities\damage_effects.py`
- `Download`
  Effect: The target must reveal whether its Defense or Special Defense Stats are lower. If the Defense Stat is lower, the user gains a +5 Damage Bonus with Physical Moves when attacking the target. If the Special Defense Stat is lower, the Damage Bonus is instead to Special Moves.
Target - Trainer or Pokmon
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Dreamspinner`
  Effect: For each Sleeping Pokmon or Trainer within 10 meters, the user gains a Tick of Hit Points.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Drizzle`
  Effect: The Weather changes to be Rainy for 5 rounds.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Drought`
  Effect: The Weather changes to be Sunny for 5 rounds.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\controllers\item_system.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Drown Out`
  Effect: The user makes a Focus Check with a DC equal to the Move's Accuracy Roll. If the user succeeds, the triggering Move fails.
Trigger - A foe uses a Move with the Sonic keyword
  References: `auto_ptu\rules\abilities\damage_effects.py`
- `Dry Skin`
  Effect: Whenever the user is hit by a damaging Fire-Type Move or ends their turn in Sunny Weather, they lose a Tick of Hit Points. The user is immune to the damage and effects of Water-Type Moves, and whenever the user is hit by a damaging Water-Type Move or ends their turn in Rainy Weather, they gain a Tick of Hit Points.
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_dry_skin_fire_tick` (phase `post_damage_followup`, holder `defender`)
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_dry_skin_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Dust Cloud`
  Effect: Connection - PoisonPowder. Whenever the user uses PoisonPowder, Sleep Powder, or Stun Spore, the user may activate this Ability to use if it as if that move have a range of Burst 1 instead.
  References: `auto_ptu\rules\battle_state.py`
- `Early Bird`
  Effect: The user gains a +3 Bonus to rolls made due to Status Afflictions.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`
- `Effect Spore`
  Effect: Roll 1d6. On a result of 1 or 2, the attacker is Poisoned. On a result of 3 or 4, the attacker is Paralyzed. On a result of 5 or 6, the attacker falls asleep.
Trigger - The user is hit by a Melee Attack
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Electric Surge`
  Effect: The Field becomes Electrified, as if affected by the Move Electric Terrain, for one full round.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Electrodash`
  Effect: The user may make a Sprint Action as a Swift Action.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Emergency Exit`
  Effect: When the user's Hit Points drop below half their maximum, their trainer may immediately recall the user and send out another Pokemon as a Free Action. If the user hasn't taken their turn yet, their replacement may act this round. [Defensive]Bonus: The user is immune to Trapped.
  References: `auto_ptu\rules\battle_state.py`
- `Empower`
  Effect: The user may use a self-targeting Status-Class Move as a Free Action.
Keywords - 2-16 Errata
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials_abilities.py`
- `Enduring Rage`
  Effect: The user may not make rolls to cure themselved of the Enraged condition.  However, while Enraged, the user gains 5 Damage Reduction.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_enduring_rage_reduces_damage` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Enfeebling Lips`
  Effect: Connection - Lovely Kiss. Whenever the user uses the Move "Lovely Kiss", they may choose a stat. If the Move successfully hits, the Pokmon or Trainer being targeted loses 2 combat stages in that stat.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Exploit`
  Effect: Whenever you deal Super-Effective Damage to a target, that target treats your damage roll as if it were increased by +5.
  Code: `auto_ptu\rules\hooks\abilities\super_effective_bonuses.py` -> `_exploit_bonus` (phase `post_result_super_effective`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\super_effective_bonuses.py`
- `Fabulous Trim`
  Effect: Furfrou's Ability depends on its current hairstyle. A Furfrou's hairstyle can be changed as an Extended Action at an appropriate hair parlor.
Star Trim: Celebrate
Diamond Trim: Defiant
Heart Trim: Cute Tears
Pharaoh Trim: Sand Veil
Kabuki Trim: Inner Focus
La Reine Trim: Intimidate
Matron Trim: Friend Guard
Dandy Trim: Moxie
Debutante Trim: Confidence
  References: `auto_ptu\rules\abilities\ability_moves.py`
- `Fade Away`
  Effect: The user becomes Invisible until the beginning of their next turn, and may immediately Shift. This Ability may be activated as an Interrupt when hit by a Physical attack; the user may declare the use of Fade Away to avoid all damage and/or effects of the move. Defensive.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Fairy Aura`
  Effect: The user and all allies have the Damage Base of their Damaging Fairy Type attacks increased by +1.
  References: `auto_ptu\rules\battle_state.py`
- `Fashion Designer`
  Effect: The user knows how to make useful accessories from mere common leaves. The user may craft one of the consumable Held Items below by activating this ability.
Lucky Leaf - Grass Type Booster for one encounter.
Tasty Reeds - Bug Type Booster for one encounter.
Dew Cup - Same Effect as an Occa Berry.
Thorn Mantle - Same Effect as a Coba Berry.
Chewy Cluster - Same Effect as Leftovers.
Decorative Twine - Roll +2d6 on any Move during a Contest.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Fiery Crash`
  Effect: Whenever the user uses a Move with the Dash keyword, they may either increase that Move's Damage Base by +2, or change the Move to be Fire-Type if it was not already. All Moves with the Dash keyword performed as Fire-Typed burn their target on 19+, or increase the effect range by +2 if they could already inflict Burn.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Filter`
  Effect: When the user is hit by a Super-Effective attack, the attack deals x1.25 damage instead of x1.5 damage. If the user is hit by a Super-Super-Effective attack, the attack deals x1.5 damage instead of x2 damage. If you have both Solid Rock and Filter, you gain 5 Damage Reduction against Super-Effective Damage. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\absorb_force_filter.py` -> `_filter_reduce_effectiveness` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\absorb_force_filter.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Flame Body`
  Effect: The attacking foe becomes Burned.
Trigger - The user is hit by a Melee Attack
- `Flame Tongue`
  Effect: Connection - Lick. The foe hit with Lick gains an Injury and becomes Burned.
Trigger - The user hits a foe with Lick.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Flare Boost`
  Effect: While Burned, the user's Special Attack is raised by 2 Combat Stages. If the user is cured of its Burn, its Special Attack is lowered by 2 Combat Stages.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Flash Fire`
  Effect: The user is immune to the damage and effects of Fire-Type attacks. If the user is hit by a Fire-Type attack, the user gains a +5 Bonus to their next Damage Roll with a Fire-Type Move. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_flash_fire_damage_boost` (phase `post_result`, holder `attacker`)
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_flash_fire_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Flower Gift`
  Effect: If it is Sunny, Flower Gift creates a 4-meter Burst. The user and all of their allies in the burst gain +2 Combat Stages, distributed among any Stat or Stats as they wish.
Keywords - Burst
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Flower Power`
  Effect: The user may perform damaging Grass Type Moves as if they were their choice of either Physical or Special.
Keywords - 2-16 Errata
  References: `auto_ptu\rules\battle_state.py`
- `Flower Veil`
  Effect: Allied Grass-Type Pokmon within 10 meters cannot have Combat Stages lowered. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Fluffy`
  Effect: The user resists damaging Melee attacks one step further, but resists Fire-Type attacks one step less. [Defensive]
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_fluffy_adjusts_damage` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Fluffy Charge`
  Effect: Connection - Charge.  Whenever the user uses Charge, they gain +1 CS to Defense.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Flutter`
  Effect: The user gains +3 Evasion until the end of their next turn and cannot be Flanked.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Flying Fly Trap`
  Effect: The Pokmon takes no damage from Ground Type Moves and Bug Type Moves. Defensive.
  References: `auto_ptu\rules\abilities\damage_effects.py`
- `Focus`
  Effect: The user gains Last Chance with Fighting.
Keywords - Last Chance
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`, `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Forecast`
  Effect: The user's Type changes depending on the weather. It changes to Fire Type if it is Sunny, Ice Type if it is Hailing, Water Type if it is Rainy, and Rock Type if there is a Sandstorm. It returns to Normal Type if it is in normal weather or foggy weather. If there are multiple Weather Effects on the field, choose one type for the user to be that corresponds with an existing Weather Effect.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Forest Lord`
  Effect: This turn, the user may originate a Grass or Ghost-Typed Move from any fully grown tree within 10 meters. Moves performed this way gain a +2 Bonus on their Accuracy Roll.
Their turn the user may originate a Grass or Ghost Type Move from any fully grown tree within 10 meters.  Moves performed this way gain a +2 Bonus on their Accuracy Rolls.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\abilities\accuracy_effects.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Forewarn`
  Effect: The Move with the highest Damage Dice Roll known by the targeted foe is revealed. If there is a tie, all tied Moves are revealed. The Moves revealed gain a -2 Penalty during Accuracy Checks when used by the target for the rest of the encounter.
Trigger - A Pokmon or Trainer
Target - A Pokmon or Trainer
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\abilities\accuracy_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Fox Fire`
  Effect: The user creates 3 Fire Wisps. Whenever the user is targeted by a foe within 6 meters, they may spend a Fire Wisp as an Interrupt to use the Move Ember against that foe as a Free Action, as if it was on their Move List.
  Code: `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py` -> `_fox_fire_interrupt` (phase `pre_damage_interrupt`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Freezing Point`
  Effect: The user gains Last Chance with Ice.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Friend Guard`
  Effect: The damage is resisted one step further. Defensive.
Trigger - An adjacent Ally takes Damage
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\defender_support_resists.py`
- `Frighten`
  Effect: Lower the target's Speed 2 Combat Stages.
Target - Pokmon or Trainer within 5 meters
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Frisk`
  Effect: The target reveals their Type, Ability, Nature, Level, and name of any Held Items they are currently holding, if any.
Target - An Adjacent Pokmon
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Frostbite`
  Effect: The user's damaging Ice Type attacks cause the target to become Slowed on 18+, and the Effect Range for Freeze on these Moves is increased by +1. If the Move does not cause Freezing, it now causes Freezing on a roll of 20.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\controllers\item_system.py`, `auto_ptu\rules\hooks\move_specials.py`, `auto_ptu\rules\item_effects.py`
- `Full Metal Body`
  Effect: The user's Combat Stages may not be lowered by the effect of foes' Feautres, Abilities, or Moves. Status Affictions may still alter their Combat Stages. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Fur Coat`
  Effect: The user resists all Physical Attacks one step further. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_support_resists.py` -> `_fur_coat_halves_physical` (phase `post_mitigation`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_support_resists.py`
- `Gale Wings`
  Effect: The user may use Flying-Type Moves as if they have the Priority keyword.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Gale Wings [SuMo Errata]`
  Effect: Connection - Quick Attack. The user may use Quick Attack as a Flying-Type Move.
Keywords - Sun/Moon Errata
  References: `auto_ptu\rules\battle_state.py`
- `Galvanize`
  Effect: If the user attacks with a Normal-Type Move, that Move is Electric-Type instead.
  References: `auto_ptu\rules\battle_state.py`
- `Gardener`
  Effect: Increase the Soil Quality of the plant by +1, as if Mulch has been applied.  This may target a Specific Plant only once per day.
Target - A yielding Plant
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Gentle Vibe`
  Effect: Burst 2.  All targets in the Burst, including the user, have their Combat Stages reset and are cured of any Volatile Status ailments.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Glisten`
  Effect: The user is immune to Fairy-Type attacks. Defensive.Bonus: If the user is hit by a damaging Fairy-Type attack, they receive +1 Defense or Special DefenseCombat Stages.
  References: `auto_ptu\rules\abilities\damage_effects.py`
- `Gluttony`
  Effect: The user may have up to three Digestion/Food Buffs at once, and may eat up to two refreshments per half hour.
  References: `auto_ptu\rules\battle_state.py`
- `Gooey`
  Effect: The triggering attacker has their Speed lowered by 1 Combat Stage.
Trigger - The user is hit by a Melee Attack.
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Gore`
  Effect: Connection - Horn Attack. Whenever the user uses Horn Attack, they may push the target away 1 meter. Additionally, Horn Attack has a Critical Range of 18-20 for the user.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Grass Pelt`
  Effect: When standing on any grassy or leafy terrain that is either Slow or Rough Terrain, the user gains +5 Damage Reduction. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_support_resists.py` -> `_grass_pelt_reduces_on_grass` (phase `post_mitigation`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\defender_support_resists.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Gulp`
  Effect: If the user is allowed to spend time fully submerged in water for at least 10 minutes, they may heal up to 25% of their Max Hit Points, and remove one Injury.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Guts`
  Effect: While suffering from Burn, Poison, Paralysis, Freezing, or while Asleep, the user's Attack is raised 2 Combat Stages. If suffering from none of these conditions, the user loses any Combat Stages gained this way.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Harvest`
  Effect: Whenever the user trades in a Digestion/Food Buff from a Berry, flip a coin. On heads, the user gains all the benefits of the Digestion/Food Buff, but the Buff is not used up. On tails, the Buff is consumed normally. While in Sunny Weather, the Buff is never consumed. The user may trade in a Digestion/Food Buff up to once per turn during an encounter, but only until they flip "Tails".
  References: `auto_ptu\rules\battle_state.py`
- `Haunt`
  Effect: The user gains Last Chance with Ghost.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Hay Fever`
  Effect: The user creates a Burst 2 or Close Blast 3 of allergenic pollen. All Trainers and Pokmon in the burst that are not Bug, Grass, or Poison Typed lose a Tick of Hit Points. This Ability cannot be activated in Rainy Weather, Sandstorms, or if it is Hailing.
Trigger - The user uses a Status Move; or the user ends their turn while Asleep.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Healer`
  Effect: The target is cured of all Status conditions.
Target - An Adjacent Pokmon or Trainer
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Heat Mirage`
  Effect: The user's Evasion is increased by +3 until the beginning of their next turn.
Trigger - The user uses a Fire-Type Move
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Heatproof`
  Effect: The user resists Fire Type moves one step further (Super-Effective Becomes Neutral, Doubly-Super Effective becomes Super-Effective, Neutral becomes Resistant, Resistant becomes doubly Resistant).
  Code: `auto_ptu\rules\hooks\abilities\heatproof.py` -> `_heatproof_reduce_fire_damage` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\heatproof.py`
- `Heavy Metal`
  Effect: When referring to Weight Classes, treat the Pokmon as if it is 2 Weight Classes higher.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`
- `Helper`
  Effect: Connection - Helping Hand. Whenever the user uses a Move that targets a single Ally, that Ally gains a +1 Bonus to Accuracy and Skill Checks until the end of the user's next turn.
  References: `auto_ptu\rules\abilities\ability_variants.py`, `auto_ptu\rules\helpers\parental_bond.py`, `auto_ptu\rules\hooks\move_specials.py`, `auto_ptu\rules\move_traits.py`, `auto_ptu\rules\targeting.py`
- `Honey Paws`
  Effect: The user may consume Honey to gain a Digestion/Food Buff as if they had consumed Leftovers. This Digestion/Food Buff does not count against their normal limit.
  References: `auto_ptu\rules\controllers\item_system.py`
- `Honey Thief`
  Effect: Connection - Bug Bite. If the user uses Bug Bite to steal the effects of a Digestion/Food Buff, they gain a Tick of Temporary Hit Points.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Huge Power`
  Effect: The Pokmon's Base Attack stat is doubled. This may double any bonuses from Nature or Vitamins, but not bonuses from Trainer Features.
  References: `auto_ptu\rules\calculations.py`
- `Hustle`
  Effect: The user receives a -2 penalty to all Accuracy Rolls with Physical Attacks, and gains a +10 Bonus to all Physical Damage Rolls.
  References: `auto_ptu\rules\calculations.py`
- `Hydration`
  Effect: At the end of the user's turn, if the weather is Rainy, the user is cured of one Status Affliction.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Hyper Cutter`
  Effect: The user's Attack Stat may not be lowered, and its Attack Combat Stages may not be lowered. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Hypnotic`
  Effect: Connection - Hypnosis. When used by the user, Hypnosis cannot miss.
  References: `auto_ptu\rules\calculations.py`
- `Ice Body`
  Effect: While Hailing, the user gains a Tick of Hit Points at the beginning of each of their turns. The user is not damaged by Hail.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Ice Shield`
  Effect: The user places up to 3 segments of Ice Wall; each segment must be continuous with another segment, and at least one must be adjacent to the user. These Ice Walls count as Blocking Terrain and last until the end of the encounter or until they are destroyed. Each Ice Wall segment is 2 meters tall, 1 meter wide, and 2 centimeters thick. Each segment has 10 Hit Points, 5 Damage Reduction, and takes damage as if it was Ice-Type.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Ignition Boost`
  Effect: The allied target gains a +5 Bonus to its damage roll with the triggering Move.  A target may not benefit from more than one instance of Ignition Boost at a time.
Trigger - An adjacent Ally uses a Fire-Type Move
  References: `auto_ptu\rules\hooks\abilities\aura_adjacent_bonuses.py`
- `Illuminate`
  Effect: Attacks that target the user have a -2 Accuracy Penalty against the user. Does not affect attackers with the Blindsense Capability. Defensive.
  References: `auto_ptu\rules\abilities\accuracy_effects.py`
- `Illusion`
  Effect: As a Standard Action, the user may mark an object, Pokmon, or Trainer. The user may have a number of targets marked equal to their Focus Rank; to mark a new target, an old mark must be forfeited. Once per round as a Free Action, the user may use illusory powers to make itself look exactly like a marked target. This may be done as the user is being released from a Pok Ball. This change is aesthetic and does not affect typing or Moves. The illusion allows the user to vaguely mimic sounds made by its marked target, but it is not capable of intelligible speech. Whenever the user is hit by a damaging Move, the Illusion is destroyed. The user may also dismiss the Illusion as a Free Action.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Immunity`
  Effect: The user cannot be Poisoned or Badly Poisoned. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Impostor`
  Effect: When Ditto is sent out, it may use the Move Transform as a free action. If the target of Transform has any modified Combat Stages, apply these Combat Stages to Ditto. One of the target's Abilities is randomly assigned to Ditto until Ditto uses Transform again.
Trigger - Ditto enters the encounter
  References: `auto_ptu\rules\battle_state.py`
- `Infiltrator`
  Effect: The user gains a +2 Bonus to Stealth Checks, does not trigger Hazards, and Blessings cannot be activated in response to its actions, and the user may bypass the effects of Substitute.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`
- `Inner Focus`
  Effect: The user cannot be Flinched. If an effect would set the user's Initiative to 0, their Initiative is not affected. Defensive.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py`
- `Insomnia`
  Effect: The user is immune to the Sleep condition, and cannot use the move Rest. Defensive.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Instinct`
  Effect: The user's default Evasion is increased by +2. Defensive.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\calculations.py`
- `Interference`
  Effect: The accuracy of all foes within 3 meters is reduced by -2 until the end of the user's next turn.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\abilities\accuracy_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Intimidate`
  Effect: Lower the target's Attack 1 Combat Stage.
Target - Pokmon or Trainer within 5 meters
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Iron Barbs`
  Effect: The attacker loses Hit Points equal to Tick of Hit Points.
Trigger - The user is hit by a damaging Melee Attack
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Iron Fist`
  Effect: The user increases the Damage Base of the following Moves by +2; Bullet Punch, Comet Punch, Dizzy Punch, Drain Punch, Dynamic Punch, Fire Punch, Meteor Mash, Shadow Punch, Ice Punch, Mach Punch, Mega Punch, Sky Uppercut, Thunder Punch, Focus Punch, Hammer Arm, and Power-Up Punch.
  References: `auto_ptu\rules\calculations.py`
- `Justified`
  Effect: The user may raise its Attack 1 Combat Stage. The user always gains a +4 bonus to Skill Checks made to Intercept.
Trigger - The user is hit by a damaging Dark Type Move
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_justified_raises_attack` (phase `post_damage`, holder `defender`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`
- `Kampfgeist`
  Effect: The user gainst STAB on Fighting Type Moves.
  References: `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Keen Eye`
  Effect: The user's Accuracy cannot be lowered, their attacks cannot have Accuracy Penalties (such as from Illuminate), the user is immune to the Blind condition (but not Total Blindness), and the user ignores any Evasion not directly derived from Stats (such as from the Instinct Ability, or from moves like Minimize).
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`
- `Klutz`
  Effect: The Pokmon ignores the effects of all held Items in its possession. The user may drop Held Items At-Will as a Free Action during their turn, even if they have Status Afflictions that prevent them from taking actions.
  References: `auto_ptu\rules\battle_state.py`
- `Klutz [SwSh]`
  Effect: Choose one of the target's Held Items or Accessory Slot Items. It is knocked to the ground.
Bonus: The Pokmon ignores the effects of all held Items in its possession. The user may drop Held Items At-Will as a Free Action during their turn, even if they have Status Afflictions that prevent them from taking actions.
Trigger - The user hits with a Melee Attack
  References: `auto_ptu\rules\battle_state.py`
- `Landslide`
  Effect: The user gains Last Chance with Ground.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Last Chance`
  Effect: The user gains Last Chance with Normal.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Leaf Gift`
  Effect: The user is adept at crafting clothes for itself out of common leaves. As an extended action, the user may craft a Leaf Suit listed below by activating this Ability; each suit has different effects on the user. The user may only wear one Leaf Suit at a time; building a new suit destroys previous suits.
Nourishing Suit - Effect: Grants the Sun Blanket and Leaf Guard Abilities.
Heavy Suit - Effect: Grants the Sturdy and Overcoat Abilities.
Vibrant Suit - Effect: Grants the Chlorophyll and Photosynthesis Abilities.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Leaf Guard`
  Effect: At the end of the User's turn, if the weather is Sunny, the user is cured of one Status Condition.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Leek Mastery`
  Effect: Connection - Acrobatics. If the user is holding a Rare Leek, they may still use Acrobatics as if they were not holding an item. The user cannot be disarmed of their Stick, nor can be it be forcefully removed by Trick, Switcheroo, Thief, or any other Moves or effects unless the user wishes it.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\move_specials_items.py`
- `Levitate`
  Effect: The Pokmon is immune to the damage and effects of Ground Type Moves, and gains a Levitate Speed of 4, or has existing Levitate Speeds increased by +2. Defensive.
  References: `auto_ptu\rules\abilities\damage_effects.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Life Force`
  Effect: The user gains a Tick of Hit Points.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Light Metal`
  Effect: When referring to Weight Classes, treat the Pokmon as if it is 2 Weight Classes lower.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`
- `Lightning Kicks`
  Effect: The user may activate this Ability to use any Move with "Kick" in the name as a Priority Move.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Lightning Rod`
  Effect: The Move is turned into a Single-Target Move and is re-directed at the user without fail, and cannot miss. This negates Lock-On or Mind Reader. Additionally, the user is immune to the damage and effects of Electric Type attacks, and each time they are hit by an Electric attack, the user's Special Attack is raised 1 Combat Stage. Defensive.
Trigger - A ranged Electric Type Move is used within 10 Meters of the user.
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_lightning_rod_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Limber`
  Effect: The user is immune to Paralysis. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Liquid Ooze`
  Effect: When the Pokmon with Liquid Ooze is damaged by Absorb, Drain Punch, Giga Drain, Horn Leech, Leech Life, Leech Seed or Mega Drain, that Move gains Recoil  and the Move's user does not gain any HP.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Liquid Voice`
  Effect: The triggering move loses the [Sonic] keyword, but gains the Friendly keyword and becomes Water Typed. If the Move was a Status Class Move, you may treat it as a Special Move with DB1.
Trigger - The user uses a Move with the [Sonic] keyword
  References: `auto_ptu\rules\battle_state.py`
- `Living Weapon`
  References: `auto_ptu\rules\battle_state.py`
- `Long Reach`
  Effect: The user may use damaging attacks as if they had a range of "8, 1 Target" instead of their usual range.
  References: `auto_ptu\rules\battle_state.py`
- `Lullaby`
  Effect: Connection - Sing. Whenever the user uses the Move "Sing", they may activate this Feature. The user then picks a Pokmon or Trainer being targeted by Sing; Sing automatically hits that target.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Lunchbox`
  Effect: The user gains 5 Temporary Hit Points. These Temporary Hit Points stack with any Temporary Hit Points granted by the triggering Buff.
Trigger - The user trades in a Digestion/Food Buff
  References: `auto_ptu\rules\battle_state.py`
- `Mach Speed`
  Effect: The user gains Last Chance with Flying.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Magic Bounce`
  Effect: The user may reflect the Move back to the attacker. This Ability may be used to change the placement and affiliation of any Hazards being set within 10 meters of the user as well. Defensive.
Trigger - The user is hit by a Status Move
  References: `auto_ptu\rules\battle_state.py`
- `Magic Guard`
  Effect: The user is immune to damage and Hit Point loss from Hazards, Weather, Status Afflictions, Vortexes, Recoil, Hay Fever, Iron Barbs, Rough Skin, and Leech Seed. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Magician`
  Effect: The user takes the target's Held Item. This Ability may not be triggered if the user is already holding a Held Item.
Trigger - The user hits a foe with a damaging Single-Target attack
  References: `auto_ptu\rules\battle_state.py`
- `Magma Armor`
  Effect: The user cannot be Frozen. Defensive.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Magnet Pull`
  Effect: Until the end of the user's next turn, the target may not move more then 8-meters away from the user and/or may not move closer than 3-meters to the user.
Target - A Steel-Type Pokmon
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Marvel Scale`
  Effect: When Asleep, Paralyzed, Burned, Frozen or Poisoned, Marvel Scale raises the user's Defense by +2 Combat Stages. The Combat Stages return to Normal if the user is cured of their status affliction.
  References: `auto_ptu\rules\battle_state.py`
- `Mega Launcher`
  Effect: The user increases the Damage Base of Aura Sphere, Dark Pulse, Dragon Pulse, and Water Pulse by +2.
  Code: `auto_ptu\rules\hooks\abilities\mega_launcher.py` -> `_mega_launcher_db_bonus` (phase `pre_damage`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\mega_launcher.py`
- `Memory Wipe`
  Effect: The user selects a Pokmon or Trainer within 10 meters. If used as a Swift Action, the last Move used by the target becomes Disabled. If used as a Standard Action, the target is Flinched. If used as an Extended Action that takes about 1 minute, it can erase up to 5 minutes that have occurred within the last 30 minutes from the target's memory.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Merciless`
  Effect: Any attacks by the user against Poisoned targets are Critical Hits. They must still hit normally.
  References: `auto_ptu\rules\calculations.py`
- `Migraine`
  Effect: Whenever the user is at 50% Hit Points or less, they gain the Telekinetic Capability and may add STAB to Psychic Type Moves.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Mimitree`
  Effect: Connection - Mimic. Whenever the user uses a Move copied by Mimic, they may choose to replace that Move with Mimic once more. When used this way, the user ignores Mimic's Frequency.
  References: `auto_ptu\rules\battle_state.py`
- `Mind Mold`
  Effect: The user gains Last Chance with Psychic.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Mini-Noses`
  Effect: The user detaches up to three Mini-Noses from themselves and places them adjacent to them on the battlefield. These Mini-Noses have HP equal to the user's level but otherwise uses their user's stats. Each Mini-Nose has a Levitate Speed of 4. The user may Shift them each round on their turn, and they may originate any Ranged Move from one of the Mini-Noses instead of themselves if they choose. If a Mini-Nose is reduced to 0 HP, it is destroyed and takes a full 24 hours to regrow, one at a time. If the user has less than three grown Mini-Noses, then this ability can only place as many on the field as are available. All Mini-Noses deactivate, but are not destroyed, if the user is Fainted. Mini-Noses cannot be made to Shift more than 5 meters away from the user; if they are forced farther away, they will automatically Shift toward the user on the user's turn.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Minus`
  Effect: The target's Special Attack is raised by +2 Combat Stages.
Target - An ally with Plus within 10 Meters
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\combat_stage_reactions.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Minus [SwSh]`
  Effect: The target loses an additional Combat Stage in one stat lowered by the triggering effect.
Trigger - A foe within 10m has Combat Stages lowered
  References: `auto_ptu\rules\hooks\abilities\combat_stage_reactions.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Miracle Mile`
  Effect: The user gains Last Chance with Fairy.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Mirror Armor`
  Effect: The user's CS are instead not lowered, and the triggering foe's CS in the affected stats are instead lowered the same amount the user's would have been.
Trigger - A foe's Move or Ability directly lowers the user's CS (including Effect Ranges, but not including things like Status)
  References: `auto_ptu\rules\battle_state.py`
- `Mojo`
  Effect: Normal Types are not immune to the user's Ghost Type Moves.
  References: `auto_ptu\rules\calculations.py`
- `Mold Breaker`
  Effect: The user ignores the effect of enemies' Defensive Abilities.
  References: `auto_ptu\rules\abilities\damage_effects.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\ability_hooks.py`
- `Moody`
  Effect: Moody must be activated whenever it is triggered. Roll 1d10 to determine a Stat to be raised by +2 Combat Stages, then roll 1d10 to determine a Stat to be lower 2 Combat Stages. 1 or 2 is Attack, 3 or 4 is Defense, 5 or 6 is Special Attack, 7 or 8 is Special Defense, 9 or 10 is Speed.
Trigger - The user joins an encounter, misses with a Move, or hurts itself in Confusion
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Motor Drive`
  Effect: The user is immune to the damage and effects of Electric Type attacks. Whenever an Electric Type attack hits the Pokmon, raise their Speed by +1 Combat Stage. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_motor_drive_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Mountain Peak`
  Effect: The user gains Last Chance with Rock.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Moxie`
  Effect: Whenever the user's Move causes a target to faint, it may raise its Attack Combat Stage by +1. You may only trigger Moxie once per Move, even if the Move causes multiple targets to faint.
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_moxie_raises_attack` (phase `post_ko`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\post_damage_effects.py`
- `Mud Dweller`
  Effect: The user resists Ground-Type and Water-Type attacks one step further.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_mud_dweller_resists_ground_water` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Multiscale`
  Effect: When at full Hit Points, when taking damage from a Move, half the total damage before applying weakness and resistance, after applying your Defenses. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_multiscale_halves_damage_at_full_hp` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Multitype`
  Effect: The user changes its Elemental Type to any of the Elemental Types. Multitype cannot be copied or disabled.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Mummy`
  Effect: Replace all of the Attacker's Abilities with Mummy until the end of the encounter.
Trigger - The user is hit by a Melee Attack
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Natural Cure`
  Effect: Whenever the user is returned to its Pok Ball or Takes A Breather, it may activate Natural Cure to cure itself of all Persistent Status Afflictions.
  References: `auto_ptu\rules\battle_state.py`
- `No Guard`
  Effect: The user may not apply any form of Evasion to avoiding melee attacks; however, the user ignores all forms of evasion when making Melee attack rolls.
  References: `auto_ptu\rules\calculations.py`
- `Normalize`
  Effect: All Moves performed by the Pokmon are considered Normal Type instead of whatever Type they normally are.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\item_catalog.py`
- `Oblivious`
  Effect: The user is immune to the Enraged and Infatuated conditions. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Odious Spray`
  Effect: Connection - Poison Gas. The user may activate this Ability when using Poison Gas to cause Poison Gas to be a single target attack with a range of 8. When used this way, Poison Gas has an AC of 2, and also flinches its target if it hits.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Omen`
  Effect: Choose a Pokmon or Trainer within 5 meters. The target's Accuracy is lowered by 2.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Overcharge`
  Effect: The user gains Last Chance with Electric.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Overcoat`
  Effect: The user is immune to Moves with the Powder Keyword, and does not take damage from any Weather that would normally cause it to take damage. Defensive.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Overgrow`
  Effect: The user gains Last Chance with Grass.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Own Tempo`
  Effect: The user is immune to Confusion. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Pack Hunt`
  Effect: The user may make a Physical Attack with an AC of 5 against the triggering foe. If the attack hits, the foe loses a Tick of Hit Points.
Trigger - An adjacent foe is damaged by an ally's Melee attack.
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_pack_hunt_counter` (phase `post_damage`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Parry`
  Effect: The attack instead misses. Defensive.
Trigger - The user is hit by a Melee Attack
  Code: `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py` -> `_parry_interrupt` (phase `pre_damage_interrupt`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\controllers\item_system.py`, `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Perception`
  Effect: You may Shift to remove yourself from the area-of-effect.
Trigger - An ally uses an area-of-effect attack that would hit you
  Code: `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py` -> `_perception_interrupt` (phase `pre_damage_interrupt`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Pickpocket`
  Effect: If the opponent has a Held Item and the user does not, the user takes the Held Item the opponent is holding.
Trigger - The user is hit by an opponent with a Melee Move
  References: `auto_ptu\rules\abilities\ability_moves.py`
- `Pickup`
  Effect: You may use Pickup as an Extended Action that requires at least 5 minutes. Roll 1d20, consult the Pickup keyword to figure out what you find!
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Pixilate`
  Effect: The Move is changed to be Fairy-Type.
Trigger - The user uses a Normal Type damaging Move.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Plus`
  Effect: The target's Special Attack is raised by +2 Combat Stages.
Target - An ally with Minus within 10 Meters
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\combat_stage_reactions.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Plus [SwSh]`
  Effect: The target gains an additional Combat Stage in one stat raised by the triggering effect.
Trigger - An ally within 10m has Combat Stages raised
  References: `auto_ptu\rules\hooks\abilities\combat_stage_reactions.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Poison Heal`
  Effect: For the rest of the encounter, while Poisoned or Badly Poisoned, the user gains a Tick of Hit Points at the beginning of each turn instead of losing any Hit Points from Poison. At the end of the encounter, the user is cured of the Poison Status. Additionally, the user does not have any Combat Stages lowered from being Poisoned.
Trigger - The user becomes Poisoned.
  References: `auto_ptu\rules\battle_state.py`
- `Poison Point`
  Effect: The attacking foe is Poisoned.
Trigger - The user is hit by a Melee Move
- `Poison Touch`
  Effect: The Pokmon's Moves which deal damage Poison Legal Targets on 19+. If a move already has a chance of Poisoning foes, Poison Touch increases the effect range by +2.
  Code: `auto_ptu\rules\hooks\abilities\contact_effects.py` -> `_poison_touch` (phase `post_contact`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\contact_effects.py`
- `Pressure`
  Effect: While within 3 meters of the user, all foes are Suppressed. This effect ends when the user is Fainted.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Prime Fury`
  Effect: The user becomes Enraged, and gains +1 Attack Combat Stage.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Prism Armor`
  Effect: The user gains +5 Damage Reduction against Super Effective-Damage. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_prism_armor_reduces_super_effective` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Protean`
  Effect: The user's Type changes to match the Type of the triggering Move. This Ability resolves before the Move is resolved (And thus you may apply STAB, and trigger other Features and Abilities appropriately).
Trigger - The user uses a Move.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Punk Rock`
  Effect: The user gains +2 DB to moves that have the Sonic keyword.
Bonus: The user resists moves with the Sonic keyword one step further. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_punk_rock_resists_sonic` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Pure Power`
  Effect: The Pokmon's base attack stat is doubled. This may double any bonuses from Nature or Vitamins, but not bonuses from Features.
  References: `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\item_effects\attacker_passives.py`
- `Quick Cloak`
  Effect: Burmy quickly builds a cloak out of nearby materials; using leaves and twigs will give it a Grass Plant Cloak, using sand and rocks will give it a Ground Sandy Cloak, and using trash or scrap will give it a Steel Trash Cloak. While in a Cloak, Burmy gains the Type associated with the Cloak as a secondary Typing, which will become permanent upon evolution into Wormadam. Cloaks are destroyed if Burmy is hit for Super-Effective Damage, or if Burmy makes a new Cloak.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Quick Curl`
  Effect: Connection - Defense Curl. The user may activate this Ability to use Defense Curl as a Swift Action.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Quick Feet`
  Effect: When Poisoned, Burned, Paralyzed, Frozen or put to Sleep, the user's Speed is raised 2 Combat Stages. The user does not lose Speed Combat Stages from Paralysis. If the user is healed all Status Conditions, their Speed is lowered appropriately.
  References: `auto_ptu\rules\calculations.py`
- `Rattled`
  Effect: The user's Speed is raised by +1 Combat Stage.
Trigger - The user is hit by a Bug, Dark, or Ghost Type Move
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_rattled_raises_speed` (phase `post_damage`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\post_damage_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Reckless`
  Effect: Increase the Damage Base of the moves Jump Kick, Hi Jump Kick, and moves with the Recoil Keyword by +2.
  References: `auto_ptu\rules\calculations.py`
- `Refreshing Veil`
  Effect: Connection - Aqua Ring. Whenever the user activates Aqua Ring, they may activate this Feature to cure themselves of all Persistent Status Effects.
  References: `auto_ptu\rules\hooks\move_specials.py`
- `Refridgerate`
  Effect: The Move is changed to be Ice Type.
Trigger - The user uses a Normal Type Damaging Move.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Regenerator`
  Effect: The user gains Hit Points equal to 1/3rd of its maximum Hit Points. Regenerator may be activated only once per Scene.
Trigger - The user is recalled into a Pokeball or Takes a Breather.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`
- `Rivalry`
  Effect: Whenever the user deals direct damage to a target of the same gender, increase the Damage dealt by +5.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\calculations.py`
- `Rock Head`
  Effect: The user ignores the Recoil keyword when attacking.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Rocket`
  Effect: The user's Sky capability is increased by +3 until the end of the user's next turn, and the user goes first on the following round, ignoring initiative; Interrupt Moves may not be used in response to their Moves that round.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Root Down`
  Effect: Connection - Ingrain. While the user has the Ingrain Coat, they may activate this Ability to gain Temporary Hit Points equal to 1/16th of their Max Hit Points.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Rough Skin`
  Effect: The attacker loses a tick of Hit Points.
Trigger - The user is hit by a damaging Melee Attack
- `Run Away`
  Effect: The user cannot be Slowed, Stuck, or Trapped. The user does not provoke Attacks of Opportunity by Shifting.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`
- `Shackle`
  Effect: Shackle creates a Burst 3. All foes in the burst have their movement capabilities halved until the end of their next turn.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Shadow Tag`
  Effect: The target's shadow becomes pinned to the target's current spot for 5 turns. During this time, the target is Slowed and Trapped, and cannot move more than 5 meters from the spot their shadow is pinned to; even being Pushed and other forced movement effects cannot force the target to Move more than 5 meters from that spot.
Target - An adjacent Trainer or Pokmon
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Shed Skin`
  Effect: The user is cured of one of Paralysis, Freezing, Burns, Poison, or Sleep.
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Shell Cannon`
  Effect: When Blastoise uses Aqua Jet, Dive, Flash Cannon, Hydro Cannon, Hydro Pump, Tackle, Waterfall, Water Gun, and Water Spout they may activate this Ability to gain +2 to their Accuracy Roll and deals +4 Bonus Damage with Damage Rolls. When using Aqua Jet, Dive, Tackle, or Waterfall, Blastoise must shift in a straight line to their target to activate this Ability, but their Overland and Swim Speeds are increased by +2 when doing so.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Shell Shield`
  Effect: Connection - Withdraw. The user may activate this Ability to use Withdraw as an Interrupt and a Free Action. The user must still use a Shift Action to stop being Withdrawn.
  Code: `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py` -> `_shell_shield_interrupt` (phase `pre_damage_interrupt`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\pre_damage_interrupts.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Skill Link`
  Effect: The Triggering Move automatically hits 5 Times.
Trigger - The user hits with a Move with the Five Strike keyword.
  References: `auto_ptu\rules\battle_state.py`
- `Sonic Courtship`
  Effect: Connection - Attract. Treat Attract as a Cone 2 Move with the Sonic keyword for this use, which effects all targets regardless of Gender.
Trigger - The user uses Attract
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Soul Heart`
  Effect: Whenever a combatant faints, the user receives +2 Special Attack Combat Stages and gains a tick of Temporary Hit Points.
  References: `auto_ptu\rules\hooks\abilities\post_damage_effects.py`
- `Soulstealer`
  Effect: The user removes one Injury from themselves and recovers 25% of their Maximum Hit Points. If the triggering attack killed its target, the user instead removes all Injuries and recovers all Hit Points.
Trigger - The user's attack causes a foe to Faint
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_soulstealer_heal` (phase `post_damage`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\post_damage_effects.py`
- `Sound Lance`
  Effect: Connection - Supersonic. The target of Supersonic takes Special Normal-Type damage equal to the user's Special Attack score. This effect functions independently of whether Supersonic hits its target.
Trigger - The user uses Supersonic
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Soundproof`
  Effect: The Pokmon is immune to Moves with the Sonic Keyword. Defensive.
  References: `auto_ptu\rules\abilities\damage_effects.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Spinning Dance`
  Effect: If not Fainted, Paralyzed, or Asleep, the user gains +1 Evasion and may immediately Shift 1 meter.
Trigger - The user is targeted by an attack, but is missed
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials_abilities.py`
- `Spray Down`
  Effect: The triggering attack's target is knocked down to ground level, and loses all Sky or Levitate Speeds for 3 turns. During this time, they may be hit by Ground-Type Moves even if normally immune.
Trigger - The user hits an airborne target with a ranged 1-target attack.
  Code: `auto_ptu\rules\hooks\abilities\post_damage_effects.py` -> `_spray_down_ground` (phase `post_damage`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\post_damage_effects.py`
- `Stamina`
  Effect: The user receives +1 Defense Combat Stage. [Defensive]
Trigger - The user is hit by a Damaging Attack
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Static`
  Effect: The attacking foe becomes Paralyzed.
Trigger - The user is hit by a Melee Attack
  References: `auto_ptu\rules\hooks\abilities\phase_effects.py`
- `Steadfast`
  Effect: The user's Speed is raised by +1 Combat Stage.
Trigger - The user is Flinched
  References: `auto_ptu\rules\battle_state.py`
- `Sticky Smoke`
  Effect: Connection - Smokescreen. All targets that begin or end their turn in the target's Smokescreen have their Accuracy lowered by -1. This penalty may occur multiple times. This stacks with the usual penalties from Smokescreen.
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Storm Drain`
  Effect: The Move is turned into a Single-Target Move and is re-directed at the User without fail, and cannot miss. This negates Lock-On or Mind Reader. Additionally, the user is immune to the damage and effects of Water Type Moves, and each time they are hit by a Water-Type Move, the User's Special Attack is raised 1 Combat Stage. Defensive.
Trigger - A ranged Water Type Move is used within 10 Meters of the user.
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_storm_drain_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Strange Tempo`
  Effect: While Confused, the user may choose either to 1) As a Free Action, not to roll for Confusion, instead acting Normally or 2) As a Standard Action, cure themselves of Confusion and gain +2 Combat Stages to the Stat of their choIce.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Sturdy`
  Effect: The Pokmon is immune to the Moves Sheer Cold, Guillotine, Horn Drill and Fissure. If any attack would lower this Pokmon to 0 Hit Points or less from full Hit Points, instead the Pokmon's Hit Point value is set to 1. This effect fails if the user's full Hit Point value is 1. Pokmon with Sturdy do not gain Injuries from Massive Damage. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\pre_apply_damage.py` -> `_sturdy_prevents_ko` (phase `pre_apply_damage`, holder `defender`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\pre_apply_damage.py`, `auto_ptu\rules\hooks\move_specials.py`
- `Sun Blanket`
  Effect: The user is one step more resistant to Fire-Type Attacks, and gains a Tick of Hit Points at the beginning of each turn in Sunny weather.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_sun_blanket_resists_fire` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials.py`, `auto_ptu\rules\hooks\move_specials_abilities.py`
- `Swarm`
  Effect: The user gains Last Chance with Bug.
Keywords - Last Chance
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Sweet Veil`
  Effect: The user and allies within 3 meters are immune to Sleep. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Swift Swim`
  Effect: While in Rainy Weather, the user gains +4 Speed Combat Stages.
  References: `auto_ptu\rules\battle_state.py`
- `Technician`
  Effect: Moves with a Damage Base of 6 or lower have their Damage Base increased by +2. This bonus always applies to Moves with the Double Strike or Fivestrike Keywords.
  References: `auto_ptu\rules\calculations.py`
- `Thick Fat`
  Effect: The user resists Fire-Type and Ice-Type attacks one step further. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_thick_fat_resists_fire_ice` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Torrent`
  Effect: The user gains Last Chance with Water.
  References: `auto_ptu\rules\hooks\abilities\last_chance_bonuses.py`
- `Tough Claws`
  Effect: The user increases the Damage Base of all Melee Moves by +2.
  References: `auto_ptu\rules\calculations.py`
- `Unnerve`
  Effect: Foes within 3 meters of you cannot gain positive Combat Stages or trade in Digestion/Food Buffs. This does not affect any Combat Stages they already have.
  References: `auto_ptu\rules\abilities\ability_moves.py`, `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\hooks\abilities\phase_effects.py`, `auto_ptu\rules\hooks\move_specials_abilities.py`
- `Volt Absorb`
  Effect: The user is immune to the damage and effects of Electric-Type attacks, and whenever they are hit with an Electric Type attack, they gain Hit Points equal to a Tick of Hit Points. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_volt_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Water Absorb`
  Effect: The user is immune to the damage and effects of Water-Type attacks, and whenever they are hit with a Water Type attack, they gain a Tick of Hit Points. Defensive.
  Code: `auto_ptu\rules\hooks\abilities\post_result_absorb.py` -> `_water_absorb` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\hooks\abilities\post_result_absorb.py`
- `Water Bubble`
  Effect: The user resists Fire-Type attacks one step further, is immune to being Burned, and may always act as though in Rainy Weather. [Defensive]Bonus: The user may attack with Water-Type Moves as if they had a range of "Melee, 1 target". If they do, that Move's Class is changed to Physical and it deals +1d6+2 damage.
  Code: `auto_ptu\rules\hooks\abilities\defender_resists.py` -> `_water_bubble_resists_fire` (phase `post_result`, holder `defender`)
  References: `auto_ptu\rules\battle_state.py`, `auto_ptu\rules\calculations.py`, `auto_ptu\rules\hooks\abilities\defender_resists.py`
- `Water Veil`
  Effect: The user is immune to Burns. Defensive.
Keywords - Immune
  References: `auto_ptu\rules\battle_state.py`
- `White Flame`
  Effect: The user may not make rolls to cure themselves from the Enraged condition. However, while Enraged, the user gains a +5 Bonus to all Damage Rolls.
  Code: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py` -> `_white_flame_enraged_bonus` (phase `post_result`, holder `attacker`)
  References: `auto_ptu\rules\hooks\abilities\attacker_damage_bonuses.py`
- `White Smoke`
  Effect: The user's Combat Stages, Evasion, or Accuracy may not be lowered except by the user's own Moves and effects. Defensive.
  References: `auto_ptu\rules\battle_state.py`
- `Wonder Guard`
  Effect: Only damaging attacks that are Super-Effective affect the Pokmon with Wonder Guard; all other damaging attacks cannot hit the user or deal damage. Wonder Guard loses its effect if the user has no weaknesses. Defensive.
  References: `auto_ptu\rules\abilities\damage_effects.py`
- `Wonder Skin`
  Effect: The user gains +6 Evasion against Status Moves. Defensive.
  References: `auto_ptu\rules\abilities\accuracy_effects.py`

## Moves (Implemented + Tested)
- `agility`
  Effect: Raise the user's Speed 2 Combat Stages.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_agility_boost` (phase `post_damage`)
- `aqua ring`
  Effect: Aqua Ring covers the user in a Coat that heals the user at the beginning of their turn. The user is healed a Tick of Hit Points each turn.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_aqua_ring` (phase `post_damage`)
- `aromatherapy`
  Effect: All allies in the burst are cured of one status condition of their choice.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_aromatherapy` (phase `post_damage`)
- `aromatic mist`
  Effect: Raise the Special Defense of all allied legal targets by +1 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_aromatic_mist` (phase `post_damage`)
- `attract`
  Effect: Attract Infatuates the target if its gender is the opposite of the user's. Attract fails when used by or against Genderless targets.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_attract_infatuate` (phase `post_damage`)
- `aura pulse`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_aura_pulse_spdef_drop` (phase `post_damage`)
- `bind`
  Effect: The user gains a +1 Bonus to Accuracy Rolls made to initiate Grapple Maneuvers, and +2 to Skill Checks made to initiate Grapple Maneuvers or gain Dominance. Whenever the user gains Dominance in a Grapple, the target of the Grapple loses a Tick of Hit Points.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bind_bonus` (phase `post_damage`)
- `bite`
  Effect: Bite Flinches the target on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bite_flinch` (phase `post_damage`)
- `blaze kick`
  Effect: Blaze Kick Burns the target on 19+ and is a Critical Hit on 18+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_blaze_kick` (phase `post_damage`)
- `blessed touch`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_blessed_touch_heal` (phase `post_damage`)
- `blue flare`
  Effect: Blue Flare Burns the target on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_blue_flare` (phase `post_damage`)
- `body slam`
  Effect: Body Slam Paralyzes the target on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_body_slam` (phase `post_damage`)
- `bolt strike`
  Effect: Bolt Strike Paralyzes the target on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bolt_strike` (phase `post_damage`)
- `bone club`
  Effect: Bone Club Flinches the target on 18+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bone_club_bone_lord` (phase `post_damage`)
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bone_club_bone_lord_errata` (phase `post_damage`)
- `bone rush`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bone_rush_bone_lord_errata` (phase `pre_damage`)
- `branch poke`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_branch_poke_speed_drop` (phase `post_damage`)
- `brutal swing`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_brutal_swing_sleep` (phase `post_damage`)
- `bubble`
  Effect: Bubble lowers the target's Speed by -1 CS on 16+..
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bubble` (phase `post_damage`)
- `bubblebeam`
  Effect: Bubblebeam lowers the target's Speed by -1 CS on 18+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bubblebeam` (phase `post_damage`)
- `bug bite`
  Effect: If the target has a stored Digestion/Food Buff or has traded in a Digestion/Food Buff this Scene, the user may gain the effects of the Digestion/Food Buff. This does no count towards the Usual limit on the user's Digestion/Food Buffs.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_honey_thief` (phase `post_damage`)
- `bug buzz`
  Effect: Bug Buzz lowers the Special Defense of all legal targets by -1 CS on 19+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bug_buzz_spdef_drop` (phase `post_damage`)
- `bulk up`
  Effect: Raise the user's Attack and Defense by +1 CS each.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_bulk_up` (phase `post_damage`)
- `captivate`
  Effect: Captivate lowers the target's Special Attack by -2 CS. Captivate may not affect something that is the same gender as the user or something that is genderless.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_captivate` (phase `post_damage`)
- `charge`
  Effect: If the user performs an Electric Attack on its next turn, add its Damage Dice Roll an extra time to the damage. Raise the user's Special Defense by +1 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_fluffy_charge` (phase `post_damage`)
- `charm`
  Effect: Lower the target's Attack by -2 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_charm` (phase `post_damage`)
- `chatter`
  Effect: Chatter confuses all targets on 16+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_chatter` (phase `post_damage`)
- `cherry power`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_cherry_power` (phase `post_damage`)
- `clay cannons`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_clay_cannons` (phase `post_damage`)
- `close combat`
  Effect: Lower the user's Defense and Special Defense by -1 CS each after damage.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_close_combat` (phase `post_damage`)
- `cloud nine`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_cloud_nine` (phase `post_damage`)
- `confide`
  Effect: Lower the target's Special Attack by -1 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_confide` (phase `post_damage`)
- `confidence`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_confidence` (phase `post_damage`)
- `confuse ray`
  Effect: The target is Confused.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_confuse_ray_confusion` (phase `post_damage`)
- `confusion`
  Effect: Confusion Confuses the target on 19+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_confusion_status` (phase `post_damage`)
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_confusion_migraine_errata` (phase `post_damage`)
- `copycat`
  Effect: Use the Move the target has used on their last turn. You may choose new targets for the Move. Copycat cannot miss.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_copy_master` (phase `post_damage`)
- `court change`
  Effect: All Blessings and Hazards swap which side that they belong to.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_court_change` (phase `post_damage`)
- `crush claw`
  Effect: Crush Claw lowers the target's Defense by -1 CS on Even-Numbered Rolls.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_crush_claw` (phase `post_damage`)
- `dark pulse`
  Effect: Dark Pulse Flinches the target on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_dark_pulse` (phase `post_damage`)
- `daze`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_daze_sleep` (phase `post_damage`)
- `decoy`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_decoy` (phase `post_damage`)
- `defend order`
  Effect: Raise the user's Defense and Special Defense by +1 CS each.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_defend_order` (phase `post_damage`)
- `defense curl`
  Effect: The user becomes Curled Up. While Curled Up, the user becomes immune to Critical Hits and gains 10 Damage Reduction. However, while Curled Up, the user is Slowed and their Accuracy is lowered by -4. The user may stop being Curled Up as a Swift Action. If the user has Rollout or Ice Ball in their Move List, they do not become Slowed while Curled Up. Furthermore, when using the Moves Rollout or Ice Ball while Curled Up, the user gains a +10 bonus to the damage rolls of those Moves and does not suffer Accuracy Penalties from being Curled Up.
September Playtest: The user's Defense is raised 1 Combat Stage and they become Curled Up until the end of the Scene or they are Recalled or Take a Breather. When using the Moves Rollout or Ice Ball while Curled Up, the user gains a +10 bonus to the damage rolls of those Moves.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_defense_curl` (phase `post_damage`)
- `defog`
  Effect: The Weather becomes Clear, and all Blessings, Coats, and Hazards are destroyed. Clear Weather is the default weather, conferring no bonuses or penalties of any sort.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_defog` (phase `post_damage`)
- `defy death`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_defy_death` (phase `post_damage`)
- `destiny bond`
  Effect: All enemy targets in the burst become Bound to the user until the end of your next turn. If a Bound target causes the user to Faint through a Damaging Attack, the Bound target immediately faints after their attack is resolved.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_destiny_bond` (phase `post_damage`)
- `diamond storm`
  Effect: Diamond Storm raises the User's Defense by +1 CS on an Even-Numbered Roll.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_diamond_storm` (phase `post_damage`)
- `discharge`
  Effect: Discharge Paralyzes all legal targets on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_discharge` (phase `post_damage`)
- `double team`
  Effect: The user gains 3 activations of Double Team. The user may either activate Double Team when being targeted by an attack to increase their Evasion by +2 against that attack or when making an attack to increase their Accuracy by +2 for that attack.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_double_team` (phase `post_damage`)
- `double-edge`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_double_edge_recoil` (phase `post_damage`)
- `download`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_download_analyze` (phase `post_damage`)
- `draco meteor`
  Effect: Lower the user's Special Attack by -2 CS after damage.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_draco_meteor` (phase `post_damage`)
- `dreamspinner`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_dreamspinner_heal` (phase `post_damage`)
- `drizzle`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_drizzle` (phase `post_damage`)
- `drought`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_drought` (phase `post_damage`)
- `earthquake`
  Effect: Earthquake can hit targets that are underground, including those using the Move Dig. *Grants Groundshaper
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_core_handled_moves` (phase `post_damage`)
- `electric surge`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_electric_surge` (phase `post_damage`)
- `electrodash`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_electrodash_sprint` (phase `post_damage`)
- `ember`
  Effect: Ember Burns the target on 18+. *Grants: Firestarter
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_ember_burn` (phase `post_damage`)
- `energy ball`
  Effect: Energy Ball lowers the foe's Special Defense 1 Combat Stage on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_energy_ball_spdef_drop` (phase `post_damage`)
- `fade away`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_fade_away` (phase `post_damage`)
- `fairy wind`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_fairy_wind_evasion_drop` (phase `post_damage`)
- `fashion designer`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_fashion_designer` (phase `post_damage`)
- `fire fang`
  Effect: Fire Fang Burns or Flinches on 18-19 during Accuracy Check; flip a coin to determine whether the foe becomes Burned or Flinched. On 20 during Accuracy Check, the foe is both Burned and Flinched.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_fire_fang_burn_flinch` (phase `post_damage`)
- `fire pledge`
  Effect: If an ally uses Grass Pledge or Water Pledge, you may use Fire Pledge as Priority (Advanced) immediately after their turn to target the same foe. If used in conjunction with Grass Pledge, Fire Hazards are created in a Brust 1 around the target. If used in conjucntion with Water Pledge, a Rainbow is created that lasts for 5 rouns. Counsult the Pledge keyword for additional details.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_pledge_combo` (phase `post_damage`)
- `flame burst`
  Effect: Any Trainers or Pokmon cardinally adjacent to the target lose 5 Hit Points
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_flame_burst_splash` (phase `post_damage`)
- `flamethrower`
  Effect: Flamethrower Burns the target on 19+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_flamethrower_burn` (phase `post_damage`)
- `flower gift`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_flower_gift` (phase `post_damage`)
- `flutter`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_flutter` (phase `post_damage`)
- `forest lord`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_forest_lord` (phase `post_damage`)
- `forewarn`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_forewarn` (phase `post_damage`)
- `fox fire`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_fox_fire` (phase `post_damage`)
- `frighten`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_frighten` (phase `post_damage`)
- `frisk`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_frisk` (phase `post_damage`)
- `gardener`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_gardener` (phase `post_damage`)
- `gentle vibe`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_gentle_vibe` (phase `post_damage`)
- `giga impact`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_giga_impact_exhaust` (phase `post_damage`)
- `glare`
  Effect: Glare Paralyzes the target.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_glare_accuracy_drop` (phase `post_damage`)
- `grass pledge`
  Effect: If an ally uses Fire Pledge or Water Pledge, you may use Grass Pledge as Priority (Advanced) immediately after their turn to target the same foe. If used in conjunction with Fire Pledge, Fire Hazards are created in a Burst 1 around the target. If used in conjunction with Water Pledge, the target and all foes adjacent to the the target are slowed and have their Speed reduced by 2 Combat Stages. Consult the Pledge keyword for additional details.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_pledge_combo` (phase `post_damage`)
- `grassy terrain`
  Effect: The area becomes Grassy for 5 rounds. While Grassy, all Pokmon and Trainers standing on the ground recover 1/10th of their maximum Hit Points at the start of every turn, and Grass-Type attacks performed by grounded Pokmon and Trainers gain a +10 bonus to Damage Rolls.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_grassy_terrain` (phase `post_damage`)
- `growl`
  Effect: Lower the Attack of all legal targets by -1 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_growl` (phase `post_damage`)
- `gulp`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_gulp` (phase `post_damage`)
- `gust`
  Effect: If the target is airborne as a result of Bounce, Fly, or Sky Drop, Gust can hit them, ignoring Range and has a Damage Base of 8 instead. *Grants: Guster
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_core_handled_moves` (phase `post_damage`)
- `heal bell`
  Effect: All targets are cured of any Persistent Status ailments.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_heal_bell` (phase `post_damage`)
- `heal order`
  Effect: The user regains HP equal to half of its full HP.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_heal_order` (phase `post_damage`)
- `healer`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_healer` (phase `post_damage`)
- `helping hand`
  Effect: Helping Hand grants the target +2 on its next Accuracy Roll this round, and +10 to its next Damage Roll this round.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_helping_hand` (phase `post_damage`)
- `high horsepower`
  Effect: High Horsepower may be used as a Free Action at the end of a Sprint Maneuver taken as a Standard Action, as long as the user Shifted at least 3 meters in a straight line towards the target. When used this way, High Horsepower gains Smite.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `horn attack`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_gore_push` (phase `post_damage`)
- `ice beam`
  Effect: Ice Beam Freezes on 19+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_ice_beam_freeze` (phase `post_damage`)
- `ice shield`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_ice_shield` (phase `post_damage`)
- `infestation`
  Effect: The target is put in a Vortex.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_vortex_moves` (phase `post_damage`)
- `ingrain`
  Effect: Ingrain applies a Coat to the user, which has the following effect; the user cannot be pushed or pulled, and cannot be switched out. At the beginning of each of the user's turn, the user gains HP equal to 1/10th of its max HP.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_ingrain` (phase `post_damage`)
- `interference`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_interference` (phase `post_damage`)
- `jaw lock`
  Effect: You may perform a Grapple Maneuver against the target as a Free Action.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_jaw_lock` (phase `post_damage`)
- `leaf gift`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_leaf_gift` (phase `post_damage`)
- `lick`
  Effect: Lick Paralyzes the target on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_lick_pre_damage` (phase `pre_damage`)
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_lick_post_damage` (phase `post_damage`)
- `life force`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_life_force` (phase `post_damage`)
- `light screen`
  Effect: Blessing - Any user affected by Light Screen may activate it when receiving Special Damage to resist the Damage one step. Light Screen may be activated 2 times, and then disappears.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_light_screen_status` (phase `post_damage`)
- `lightning kicks`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_lightning_kicks` (phase `post_damage`)
- `lovely kiss`
  Effect: The target fall Asleep.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_enfeebling_lips` (phase `post_damage`)
- `low kick`
  Effect: Low Kick's Damage Base is equal to twice the target's Weight Class.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `lullaby`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_lullaby` (phase `post_damage`)
- `magnet pull`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_magnet_pull` (phase `post_damage`)
- `magnitude`
  Effect: When you use Magnitude, roll 1d6. Magnitude's Damage Base is equal to 5+X, where X is the value of the d6. Magnitude can hit targets that are underground, including those using the Move Dig. *Grants: Groundshaper
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_magnitude_log` (phase `end_action`)
- `memory wipe`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_memory_wipe` (phase `post_damage`)
- `mimic`
  Effect: Choose a Move that the target has used during the encounter. For the remainder of the encounter, that Move replaces Mimic on the user's Move List. Mimic cannot miss.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mimic` (phase `post_damage`)
- `mini-noses`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mini_noses` (phase `post_damage`)
- `minus`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_minus` (phase `post_damage`)
- `moonlight`
  Effect: The user regains HP equal to half of its full HP. If it is Sunny, the user gains 2/3 of its full HP. If it is Rainy, Sand Storming, or Hailing, the user gains 1/4 of its full HP.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_moonlight` (phase `post_damage`)
- `morning sun`
  Effect: The user regains Hit Points equal to half of its full Hit Point value. If it is Sunny, the user gains 2/3 of its full Hit Point value. If it is Rainy, Sand Storming or Hailing the user gains 1/4 of their full Hit Point value.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_morning_sun` (phase `post_damage`)
- `mountain gale`
  Effect: The target is Flinched on a 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mountain_gale` (phase `post_damage`)
- `mud bomb`
  Effect: The target's Accuracy is lowered by -1 on 16+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mud_bomb` (phase `post_damage`)
- `mud shot`
  Effect: The target's Speed is lowed by -1 Combat Stage.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mud_shot_speed_drop` (phase `post_damage`)
- `mud slap`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mud_slap_accuracy_drop` (phase `post_damage`)
- `mud-slap`
  Effect: The target's Accuracy is lowered by -1.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mud_slap_accuracy_drop` (phase `post_damage`)
- `muddy water`
  Effect: As a Shift Action, the user may Move to any open square in Muddy Water's area of effect without provoking any Attacks of Opportunity. On 16+, the Accuracy of all targets is lowered by 1.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_muddy_water` (phase `post_damage`)
- `mystical fire`
  Effect: Mystical Fire lowers the target's Special Attack by 1 Combat Stage.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mystical_fire` (phase `post_damage`)
- `mystical power`
  Effect: The user receives +1 Combat Stage in their highest non-HP stat.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_mystical_power` (phase `post_damage`)
- `name`
  Effect: Effects
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `nasty plot`
  Effect: Raise the user's Special Attack by +2 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_nasty_plot` (phase `post_damage`)
- `needle arm`
  Effect: Needle Arm Flinches the target on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_needle_arm` (phase `post_damage`)
- `night daze`
  Effect: Night Daze lowers the target's Accuracy by -1 on 13+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_night_daze` (phase `post_damage`)
- `nightmare`
  Effect: Nightmare can only hit Legal Targets that are Asleep. The target gains Bad Sleep.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_nightmare_bad_sleep` (phase `post_damage`)
- `octazooka`
  Effect: Octazooka lowers the target's Accuracy by -1 on an Even-Numbered Roll.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_octazooka_accuracy_drop` (phase `post_damage`)
- `octolock`
  Effect: The user initiates a Grapple Maneuver with the target, which automatically hits. If successful, until the user no longer has Dominance in the grapple, the target is Trapped and loses 1 CS in Defense and Special Defense at the end of each of their turns.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_octolock_grapple` (phase `post_damage`)
- `odor sleuth`
  Effect: Odor Sleuth may be activated as a Swift Action on the user's turn. For the rest of the turn, the user's Normal-Type and Fighting-Type Moves can hit and affect Ghost-Type targets, and the user can see through the Illusion Ability, Moves with the Illusion keyword, and effects created by the Illusionist Capability, ignoring all effects from those.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_odor_sleuth_foresight` (phase `post_damage`)
- `omen`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_omen` (phase `post_damage`)
- `overdrive`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_overdrive_heal` (phase `post_damage`)
- `pack hunt`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_pack_hunt` (phase `post_damage`)
- `payback`
  Effect: If the target hit the user with a Damaging Move on the previous turn, Payback has a Damage Base of 10 (3d8+10 / 24) instead.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_payback_noop` (phase `post_damage`)
- `pickup`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_pickup_roll` (phase `post_damage`)
- `pierce!`
  Effect: Pierce deals an additional +10 damage against targets with Damage Reduction.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `plus`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_plus` (phase `post_damage`)
- `poison gas`
  Effect: Poison Gas Poisons all legal targets.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_poison_gas` (phase `post_damage`)
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_poison_gas_odious` (phase `post_damage`)
- `poison powder`
  Effect: The target is Poisoned.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_poison_powder` (phase `post_damage`)
- `poison sting`
  Effect: Poison Sting Poisons the target on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_poison_sting` (phase `post_damage`)
- `prime fury`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_prime_fury` (phase `post_damage`)
- `psybeam`
  Effect: Psybeam Confuses the target on 19+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_psybeam_confuse` (phase `post_damage`)
- `psychic`
  Effect: The target is Pushed 1 meter in any direction. Psychic lowers the target's Special Defense 1 Combat Stage on 17+.  Grants Telekinetic.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_psychic_spdef_drop` (phase `post_damage`)
- `quick attack`
  Effect: None.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_quick_attack_priority` (phase `post_damage`)
- `quick cloak`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_quick_cloak_manual` (phase `post_damage`)
- `quick curl`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_quick_curl` (phase `post_damage`)
- `rapid spin`
  Effect: Rapid Spin destroys all Hazards within 5 meters, removes Leech Seeds, and removes the user's Trapped or Stuck status.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rapid_spin_clear` (phase `post_damage`)
- `rattled`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rattled` (phase `post_damage`)
- `recycle`
  Effect: The effect of a consumable item used earlier in the encounter is used again as if it had not been destroyed. The item is still gone.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_recycle` (phase `post_damage`)
- `reflect type`
  Effect: Reflect Type changes one of the user's Types into one Type of your choice that the target has for the rest of the scene.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_reflect_type` (phase `post_damage`)
- `refresh`
  Effect: The user is cured of all Poison, Burns, and Paralysis.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_refresh` (phase `post_damage`)
- `relic song`
  Effect: All legal targets fall Asleep on 16+. As long as Meloetta knows Relic Song, it may change between Aria Form and Step Form as a Swift Action when using Relic Song or as a Standard Action otherwise. Both Aria and Step Form must be statted with the same HP Stat.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_relic_song_sleep` (phase `post_damage`)
- `rending spell`
  Effect: The target loses a Tick of Hit Points on 16+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rending_spell` (phase `post_damage`)
- `resonance beam`
  Effect: All targets have their Special Defense lowered by 1 Combat Stage on 20+. This Effect Range is extended by +1 for each foe targeted by this Move.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_resonance_beam` (phase `post_damage`)
- `rest`
  Effect: The user is set to their full Hit Point value. The user is cured of any Status ailments. Then, the user falls Asleep. The user cannot make Sleep Checks at the beginning of their turn. They are cured of the Sleep at the end of their turn in 2 rounds.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rest` (phase `post_damage`)
- `retaliate`
  Effect: Retaliate's DB is doubled to DB 14 (4d10+15 / 40) if an ally has been Fainted by a Damaging Move used by the Target in the last 2 rounds of Combat.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_retaliate_boost` (phase `post_damage`)
- `return`
  Effect: Return's DB is equal to 3 plus the user's Loyalty Value.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_return_db` (phase `post_damage`)
- `revelation dance`
  Effect: Revelation Dance is the same Type as the user's primary Type (aka the first one in its Pokedex listing). Revelation Dance deals +5 Bonus Damage for every other Dance Move used by the user this round, to a maximum of +15.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_revelation_dance` (phase `post_damage`)
- `revenge`
  Effect: When declaring Revenge, the user does nothing and may not Shift. At the end of the round, the user may Shift and use Revenge. If the target damaged the user this round, Revenge has a Damage Base of 12 (4d10+15 / 40).
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_revenge_boost` (phase `post_damage`)
- `reversal`
  Effect: For each Injury the user has, Reversal's Damage Base is increased by +1.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_reversal_bonus` (phase `post_damage`)
- `riposte`
  Effect: Trigger: Your Target misses you with a melee Attack.
Limitations: Melee or Short-Ranged Weapons Only
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_riposte_requires_trigger` (phase `pre_damage`)
- `rising voltage`
  Effect: After Rising Voltage is resolved, you may create Electric Terrain in a Blast 7, centered on the user, that lasts for 5 turns. Any creatures in those spaces are affected as if by the Field Move Electric Terrain, rather than any other Field Move. This Effect may trigger only once per Scene.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rising_voltage` (phase `post_damage`)
- `roar`
  Effect: When declaring Roar, the user does nothing. At the end of the round, the user Shifts and uses Roar. Targets hit by Roar immediately Shift away from the user using their highest useable movement capability, towards their Trainer if possible. If the target is an owned Pokmon and ends this shift within 6 meters of their Pok Ball, they are immediately recalled to their Pok Ball. If that Trainer sends out a replacement, they do not lose their Command action.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_roar_force` (phase `post_damage`)
- `rock climb`
  Effect: Rock Climb Confuses the target on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rock_climb_confuse` (phase `post_damage`)
- `rock polish`
  Effect: Raise the user's Speed by +2 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rock_polish` (phase `post_damage`)
- `rock slide`
  Effect: Rock Slide Flinches all legal targets on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rock_slide_flinch` (phase `post_damage`)
- `rock smash`
  Effect: Rock Smash lowers the target's Defense 1 Combat Stage on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rock_smash_lower_def` (phase `post_damage`)
- `rock throw`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `rock tomb`
  Effect: Rock Tomb lowers the target's Speed by -1 CS. *Grants Materializer
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rock_tomb_speed_drop` (phase `post_damage`)
- `rocket`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rocket` (phase `post_damage`)
- `rolling kick`
  Effect: Rolling Kick Flinches the target on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_rolling_kick_flinch` (phase `post_damage`)
- `root down`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_root_down` (phase `post_damage`)
- `sand attack`
  Effect: The target is Blinded until the end of their next turn.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_sand_attack_lower_accuracy` (phase `post_damage`)
- `scratch`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `screech`
  Effect: Lower the Defense of all legal targets by -2 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_screech_drop` (phase `post_damage`)
- `seed bomb`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_noop_mark_handled` (phase `post_damage`)
- `shackle`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_shackle` (phase `post_damage`)
- `shadow ball`
  Effect: Shadow Ball lowers the target's Special Defense by -1 CS on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_shadow_ball_spdef_drop` (phase `post_damage`)
- `shadow bone`
  Effect: Lower the target's Defense by -1 CS on a 17+. Counts as a Bone Move for Cubone/Marowak's Abilities, etc.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_shadow_bone_def_drop` (phase `post_damage`)
- `shadow tag`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_shadow_tag_anchor` (phase `post_damage`)
- `sharpen`
  Effect: Raise the user's Attack by +1 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_sharpen_attack_raise` (phase `post_damage`)
- `shell shield`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_shell_shield_ready` (phase `post_damage`)
- `sing`
  Effect: All legal Targets fall Asleep. On a miss, Sing instead causes targets to become Slowed and suffer a -2 penalty to their Evasion until the end of the user's next turn.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_sing_sleep` (phase `post_damage`)
- `slash`
  Effect: Slash is a Critical Hit on 18+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_slash_crit_log` (phase `end_action`)
- `sleep powder`
  Effect: The target falls Asleep.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_sleep_powder_sleep` (phase `post_damage`)
- `smokescreen`
  Effect: Smokescreen creates a blast of Smoke that covers the target area; the Smoke persists until the end of the encounter, or until Defog or Whirlwind are used. All targets attacking from or into the Smoke receive a -3 penalty to Accuracy.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_smokescreen` (phase `post_damage`)
- `snore`
  Effect: Snore Flinches all legal targets on 15+. Snore may only be used by Sleeping users.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_snore_flinch` (phase `post_damage`)
- `solar beam`
  Effect: Set-Up Effect: If the weather is not Sunny, the user's turn ends. If the weather is Sunny, immediately proceed to the Resolution Effect instead and this Move loses the Set-Up keyword. Resolution Effect: The user attacks with Solar Beam. If the weather is Rainy, Sandstorming, or Hailing, Solar Beam's Damage Base is lowered to 6 (2d6+8 / 15).
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_core_handled_moves` (phase `post_damage`)
- `sonic courtship`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_sonic_courtship_ready` (phase `post_damage`)
- `sound lance`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_sound_lance_ready` (phase `post_damage`)
- `spark`
  Effect: Spark Paralyzes the target on 15+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_spark_paralyze` (phase `post_damage`)
- `spore`
  Effect: The target falls Asleep.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_spore_sleep` (phase `post_damage`)
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_spore_sleep` (phase `post_damage`)
- `stamina`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_stamina` (phase `post_damage`)
- `stealth rock`
  Effect: Set 4 square meters of Stealth Rock hazards within 6 meters. If a foe moves within 2 meters of a space occupied by Rocks, move at most one Rock to the offender, then destroy the Rock. When that happens, the Stealth Rock causes a foe to lose a Tick of Hit Points. Stealth Rock is considered to be dealing damage; Apply Weakness and Resistance. Do not apply stats. A Pokmon who has been hit by a Stealth Rock Hazard cannot get hit by another in the same encounter until it is returned to a Pok Ball and then sent back out. *Grants Materializer
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_stealth_rock` (phase `post_damage`)
- `steel roller`
  Effect: Legal targets hit by Steel Roller are Tripped on a roll of 15+. Any Hazards in spaces Passed through or adjacent to those spaces are removed (they are removed before they can affect the user). If the user moves through an area of Terrain, or a Field-range Terrain is active, those effects immediately end.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_steel_roller` (phase `post_damage`)
- `strange tempo`
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_strange_tempo` (phase `post_damage`)
- `struggle`
  Effect: --
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_struggle_log` (phase `end_action`)
- `supersonic`
  Effect: The target becomes Confused. On miss, the target suffers a -2 penalty to Accuracy Rolls for one full round.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_supersonic_confuse` (phase `post_damage`)
- `surging strikes`
  Effect: If Surging Strikes hits, it is a Critical Hit. After attacking with Surging Strikes, hit or miss, the user may Shift 2m, ignoring Attacks of Opportunity from their target. It may then make an additional attack with this Move on a different target. This effect may be repeated a second time, the third attack targeting a creature that has not yet been targeted by either prior attack. Before making each attack roll, the user can elect to give up triggering all remaining additional shifts and attacks. Surging Strikes gains +3 DB for each attack that is given up.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_surging_strikes_log` (phase `post_damage`)
- `swallow`
  Effect: If the user's Stockpiled count is 1, they are healed 25% of their full Hit Point value; if their Stockpiled count is 2, they are healed half of their full Hit Point value; if their Stockpiled count is 3, they are healed back to full Hit Points. After using Swallow, the user's Stockpiled count is set to 0. If the user has no Stockpiled count, Swallow does nothing.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_swallow_big_swallow` (phase `post_damage`)
- `swift`
  Effect: Swift cannot Miss.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_swift_always_hits` (phase `end_action`)
- `tail whip`
  Effect: All legal targets have their Defense lowered by -1 CS.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_tail_whip_def_drop` (phase `post_damage`)
- `thunder fang`
  Effect: Thunder Fang Paralyzes or Flinches on 18-19; flip a coin to determine whether the foe becomes Paralyzed or Flinched. On 20, the foe is both Paralyzed and Flinched.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_thunder_fang` (phase `post_damage`)
- `thunder shock`
  Effect: Thunder Shock Paralyzes the target on 17+. *Grants Zapper
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_thunder_shock_paralyze` (phase `post_damage`)
- `thunder wave`
  Effect: Thunder Wave cannot miss. Thunder Wave Paralyzes the target. Pokmon immune to Electric Attacks are immune to Thunder Wave's effects.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_thunder_wave_paralyze` (phase `post_damage`)
- `thunderbolt`
  Effect: Thunderbolt Paralyzes the target on 19+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_thunderbolt_paralyze` (phase `post_damage`)
- `toxic`
  Effect: The target is Badly Poisoned. If the user is Poison Type, Toxic cannot miss.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_toxic_badly_poison` (phase `post_damage`)
- `u-turn`
  Effect: The user deals damage and then is immediately recalled to its Pok Ball in the same turn. A New Pokmon may immediately be sent out. Using U-Turn lets a Trapped user be recalled.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_u_turn_recall` (phase `end_action`)
- `volt switch`
  Effect: If Volt Switch successfully hits its target, the user deals damage and then immediately is returned to its Poke Ball in the same turn. A New Pokemon may immediately be sent out. Using Volt Switch lets a Trapped user be recalled
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_volt_switch_recall` (phase `end_action`)
- `water gun`
  Effect: *Grants Fountain
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_water_gun_fountain` (phase `end_action`)
- `water pulse`
  Effect: Water Pulse Confuses the target on 17+.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_water_pulse_confuse` (phase `post_damage`)
- `whirlwind`
  Effect: All targets are pushed X meters, where X is 8 minus their weight class. If the Line targets into a Smokescreen, the smoke is dispersed. All hazards in the Whirlwind are destroyed.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_blow_away_tick` (phase `post_damage`)
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_blow_away_errata` (phase `post_damage`)
- `will-o-wisp`
  Effect: The target is Burned.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_will_o_wisp_burn` (phase `post_damage`)
- `wing attack`
  Effect: None.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_wing_attack_guster` (phase `end_action`)
- `wrap`
  Effect: The user gains a +1 Bonus to Accuracy Rolls made to initiate Grapple Maneuvers, and +2 to Skill Checks made to initiate Grapple Maneuvers or gain Dominance. Whenever the user gains Dominance in a Grapple, the target of the Grapple loses a Tick of Hit Points.
  Code: `auto_ptu\rules\hooks\move_specials.py` -> `_wrap_bonus` (phase `post_damage`)

## Generic Move Text Resolution
Moves without explicit handlers rely on `auto_ptu/rules/hooks/move_specials.py`.
These generic resolvers parse effect text for:
- Status inflictions with thresholds (e.g., “burns on 17+”)
- Always-on status inflictions
- Sleep inflictions
- Stat raises/lowers with explicit CS amounts
- Critical hit thresholds and even-roll crits
- “Cannot miss / always hit”
