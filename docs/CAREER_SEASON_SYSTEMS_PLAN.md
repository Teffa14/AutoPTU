# Career season systems plan

This document defines the next Career systems after the battle-transition and training slice. The implementation must keep the deterministic Career contract and must not make the PTU battle engine depend on UI state.

## Seasonal club market

Every new season opens with a club market before normal season decisions. The player receives three deterministic offers from clubs in the current region and league. Each offer exposes salary, contract length, loan slots, loan Pokémon, and one club identity perk. Staying with the current club remains an explicit option when renewal is available.

Club assignment must no longer silently choose the first eligible club. A season cannot enter its decision calendar until the player signs a club or explicitly chooses to compete independently when that league allows it.

Club Pokémon are loans. A loan has its own stable Pokémon identity for that season, can be placed in the active six, can receive temporary season training, and is removed when the club relationship ends. Loan Pokémon never count as captured or permanently owned and cannot be moved into permanent PC storage. The timeline records who supplied the Pokémon and when it returned.

## Sponsor market

Sponsors are separate from clubs. Reputation, media decisions, league and prior sponsor performance determine which offers appear. A sponsor offer contains a guaranteed payment, a season objective, an objective bonus, and optionally a gameplay perk or supplied item.

A trainer may sign one primary sponsor per season. Sponsor objectives must be evaluated from already authoritative Career events such as wins, captures, use of a roster category, health, or decision families. No sponsor may directly alter a resolved battle transcript after the fact.

## Capture expansion

Capture opportunities continue after the active roster reaches six because PC storage already exists. The current six-Pokémon gate must be removed.

Normal capture decisions should show a broader encounter board rather than only three fixed rarity outcomes. The target is four to six deterministic candidates, gated by region, scouting, Pokédex level, league and rarity. A catch spends a Poké Ball, creates a permanent Career Pokémon, and sends overflow to PC without forcing the player to discard an existing Pokémon.

Capture content should occur regularly throughout a long career. Scouting and Pokédex progression should improve the quality and breadth of the encounter pool rather than merely changing a hidden modifier.

## Acceptance rules

- Same run seed and same choices produce the same offers and encounters.
- Club loans cannot become permanent captures accidentally.
- Changing clubs cleans up expired loans before the next schedule is built.
- Sponsor rewards and failures are visible in the timeline and season summary.
- Capture opportunities still occur when six or more Pokémon are owned.
- The active battle roster remains capped at six while PC storage remains unlimited.
- Existing saves migrate without losing owned Pokémon, contracts, money or timeline history.
