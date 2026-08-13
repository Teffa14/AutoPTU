import { describe, expect, it } from "vitest";

import { spriteSlug } from "./spriteUrl";

describe("career sprite URLs", () => {
  it("matches the static pack slug used by the Python asset builder", () => {
    expect(spriteSlug("Farfetch'd Galar")).toBe("farfetchd-galar");
    expect(spriteSlug("Flabébé")).toBe("flabebe");
    expect(spriteSlug("Nidoran ♀")).toBe("nidoranf");
    expect(spriteSlug("Vulpix Alolan")).toBe("vulpix-alola");
  });
});
