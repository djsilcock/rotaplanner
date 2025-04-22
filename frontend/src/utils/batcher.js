//utility functions
import { throttle } from "lodash";

export class Batcher {
  #fetchFn;
  #keySerialiser;
  #handleAdditionalData;
  #handleMissingData;
  #processData;
  #timeout;
  #promiseCallbacks;
  #keys;
  #invoke;

  /**
   * Creates an instance of Batcher.
   * @param {Object} options - The options for the Batcher.
   * @param {Function} options.fetchFn - The function to fetch data.
   * @param {Function} [options.keySerialiser=JSON.stringify] - Function to serialize keys.
   * @param {Function} [options.handleAdditionalData=() => {}] - Function to handle unsolicited data from the server.
   * @param {Function} [options.handleMissingData] - Function to handle missing data. Default implementation throws error
   * @param {Function} [options.extractKey=(dataItem) => dataItem.id] - Function to extract key from data item.
   * @param {number} [options.timeout=50] - Timeout for throttling in milliseconds.
   */
  constructor({
    fetchFn,
    keySerialiser = JSON.stringify,
    handleAdditionalData = () => {},
    handleMissingData = (key, data) => {
      throw `${key} is not in the server response`;
    },
    processData = (data) => data.map((item) => [item.id, item]),
    timeout = 50,
  }) {
    this.#fetchFn = fetchFn;
    this.#keySerialiser = keySerialiser;
    this.#handleAdditionalData = handleAdditionalData;
    this.#handleMissingData = handleMissingData;
    this.#processData = processData;
    this.#timeout = timeout;
    this.#promiseCallbacks = new Map();
    this.#keys = new Set();
    this.#invoke = throttle(this.#doInvoke.bind(this), this.#timeout, {
      leading: false,
      trailing: true,
    });
  }

  async #doInvoke() {
    const keysToFetch = Array.from(this.#keys);
    const callbackMap = new Map(this.#promiseCallbacks);
    this.#keys.clear();
    this.#promiseCallbacks.clear();
    try {
      const fetchedData = await this.#fetchFn(keysToFetch);
      const results = this.#processData(fetchedData);
      results.forEach(([key, dataItem]) => {
        const serialisedKey = this.#keySerialiser(key);
        if (callbackMap.has(serialisedKey)) {
          callbackMap.get(serialisedKey).resolve(dataItem);
          callbackMap.delete(serialisedKey);
        } else {
          this.#handleAdditionalData(key, dataItem);
        }
      });
      callbackMap.forEach(({ key, resolve, reject }) => {
        try {
          resolve(this.#handleMissingData(key, fetchedData));
        } catch (e) {
          console.error(e);
          reject(e);
        }
      });
    } catch (error) {
      console.error(error);
      callbackMap.forEach(({ reject }) => reject(error));
    }
  }
  /**
   * Fetches data for the given key.
   * If the key is not already being fetched, it adds the key to the batch and schedules a fetch.
   * Returns a promise that resolves with the fetched data or rejects with an error.
   *
   * @param {any} key - The key for which to fetch data.
   * @returns {Promise<any>} - A promise that resolves with the fetched data or rejects with an error.
   */
  fetch(key) {
    const serialisedKey = this.#keySerialiser(key);
    if (!this.#promiseCallbacks.has(serialisedKey)) {
      this.#keys.add(key);
      const { resolve, reject, promise } = this.#createPromiseWithResolvers();
      this.#promiseCallbacks.set(serialisedKey, {
        key,
        resolve,
        reject,
        promise,
      });
    }
    this.#invoke();
    return this.#promiseCallbacks.get(serialisedKey).promise;
  }

  #createPromiseWithResolvers() {
    let resolve, reject;
    const promise = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { resolve, reject, promise };
  }
}
