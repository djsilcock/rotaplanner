import { describe, it, expect, beforeEach, vi } from "vitest";
import { Batcher } from "./batcher";

describe("Batcher", () => {
  let fetchFn;
  let batcher;

  beforeEach(() => {
    fetchFn = vi.fn().mockResolvedValue([
      { id: 1, name: "Item 1" },
      { id: 2, name: "Item 2" },
      { id: 3, name: "Item 3" },
    ]);
    batcher = new Batcher({ fetchFn });
  });

  it("should fetch data for a single key", async () => {
    const data = await batcher.fetch(1);
    expect(data).toEqual({ id: 1, name: "Item 1" });
    expect(fetchFn).toHaveBeenCalledWith([1]);
  });

  it("should batch multiple keys into a single fetch", async () => {
    const promise1 = batcher.fetch(1);
    const promise2 = batcher.fetch(2);

    const data1 = await promise1;
    const data2 = await promise2;

    expect(data1).toEqual({ id: 1, name: "Item 1" });
    expect(data2).toEqual({ id: 2, name: "Item 2" });

    expect(fetchFn).toHaveBeenCalledWith([1, 2]);
  });

  it("should throw error if response is not supplied by the server", async () => {
    batcher = new Batcher({ fetchFn });

    await batcher.fetch(1);
    await expect(batcher.fetch(4)).rejects.toThrow(); // This key is not in the mockResolvedValue
  });
  it("should return default response if missing data handler given and data not supplied by the server", async () => {
    batcher = new Batcher({ fetchFn, handleMissingData: (key) => key });

    await batcher.fetch(1);
    const data4 = await batcher.fetch(4);
    expect(data4).toEqual(4); // This key is not in the mockResolvedValue
  });

  it("should handle additional data", async () => {
    const handleAdditionalData = vi.fn();
    batcher = new Batcher({ fetchFn, handleAdditionalData });

    await batcher.fetch(1);
    await batcher.fetch(2); // This key is not in the mockResolvedValue

    expect(handleAdditionalData).toHaveBeenCalledWith(3, {
      id: 3,
      name: "Item 3",
    });
  });

  it("should reject promise on fetch error", async () => {
    fetchFn.mockRejectedValue(new Error("Fetch error"));
    await expect(batcher.fetch(1)).rejects.toThrow("Fetch error");
  });
});
