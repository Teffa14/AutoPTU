import type { BattleTranscript } from "./types";

const databaseName = "autoptu-career-replays-v1";

export async function saveReplay(transcript: BattleTranscript): Promise<void> {
  if (!("indexedDB" in window)) return;
  const database = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction("replays", "readwrite");
    transaction.objectStore("replays").put({ id: transcript.battle_id, savedAt: Date.now(), transcript });
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  database.close();
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(databaseName, 1);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains("replays")) database.createObjectStore("replays", { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
