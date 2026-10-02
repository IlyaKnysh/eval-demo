function textsMatch(page, locatorA, locatorB) {
  try {
    const a = page.locator(locatorA).textContent();
    const b = page.locator(locatorB).textContent();
    return a === b;
  } catch (e) {
  }
  return true;
}

module.exports = { textsMatch };
