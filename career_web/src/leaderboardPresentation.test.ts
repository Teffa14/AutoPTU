import { describe, expect, it } from "vitest";

import { leaderboardTrainerName } from "./leaderboardPresentation";

describe("leaderboardTrainerName", () => {
  it("keeps a visible legacy handle when trainer_name is blank or corrupt", () => {
    expect(leaderboardTrainerName({ trainer_name: "   ", handle: "  Red   Campo  " })).toBe("Red Campo");
    expect(leaderboardTrainerName({ trainer_name: "null", handle: "Blue" })).toBe("Blue");
    expect(leaderboardTrainerName({ trainer_name: "NaN", handle: "Leaf" })).toBe("Leaf");
  });

  it("never renders browser corruption tokens when both names are unusable", () => {
    expect(leaderboardTrainerName({ trainer_name: undefined, handle: undefined })).toBe("Trainer");
    expect(leaderboardTrainerName({ trainer_name: null, handle: "   " })).toBe("Trainer");
  });

  it("normalizes visible whitespace for stable public identity", () => {
    expect(leaderboardTrainerName({ trainer_name: "  Mayra   Sol  ", handle: "legacy" })).toBe("Mayra Sol");
  });
});
