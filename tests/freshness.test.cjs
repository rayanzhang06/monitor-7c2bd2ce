const test = require('node:test');
const assert = require('node:assert/strict');
const { assessFreshness } = require('../site/freshness.js');
const calendar = { valid_until: '2026-09-30', closes: [
  { date: '2026-09-17', close: '2026-09-17T07:00:00Z' },
  { date: '2026-09-18', close: '2026-09-18T07:00:00Z' },
  { date: '2026-09-21', close: '2026-09-21T07:00:00Z' }
] };
const snapshot = { authority: {status:'passed'}, freshness:{data_end:'2026-09-18',required_session:'2026-09-18'}, account:{valuation_date:'2026-09-18',observed_at:'2026-09-19T00:00:00Z'} };
test('weekend uses Friday close, not previous natural day', () => {
  assert.equal(assessFreshness(snapshot, calendar, new Date('2026-09-19T01:00:00Z')).isFresh, true);
});
test('old captured freshness cannot keep a page green', () => {
  const state = assessFreshness(snapshot, calendar, new Date('2026-09-21T08:00:00Z'));
  assert.equal(state.isFresh, false);
  assert.equal(state.required, '2026-09-21');
});
test('expired calendar cannot imply freshness', () => {
  assert.equal(assessFreshness(snapshot, calendar, new Date('2026-10-01T00:00:00Z')).isFresh, false);
});
