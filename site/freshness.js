(function (root) {
  function assessFreshness(data, calendar, now = new Date()) {
    const today = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    const available = calendar && today <= calendar.valid_until;
    const completed = available ? calendar.closes.filter(item => Date.parse(item.close) <= now.getTime()) : [];
    const required = completed.at(-1)?.date || null;
    const captureAge = now.getTime() - Date.parse(data.account?.observed_at || '');
    const accountFresh = data.account?.status !== 'stale' && data.account?.valuation_date === required && captureAge >= 0 && captureAge <= 86400000;
    const modelFresh = Boolean(required) && data.authority?.status === 'passed' && data.freshness?.data_end === required;
    // Display SLA only: every completed close is due the next morning at 08:30 +08.
    // Do not change the production latest-completed-session gate above.
    const due = completed.filter(item => {
      const nextMorning = Date.parse(item.date + 'T00:30:00Z') + 86400000;
      return nextMorning <= now.getTime();
    }).at(-1)?.date || null;
    const modelOnSchedule = Boolean(due) && data.authority?.status === 'passed' && data.freshness?.data_end >= due;
    return {required, due, modelFresh, accountFresh, modelOnSchedule,
      modelOverdue:Boolean(due) && !modelOnSchedule, isFresh:modelFresh && accountFresh};
  }
  root.assessFreshness = assessFreshness;
  if (typeof module !== 'undefined') module.exports = {assessFreshness};
})(typeof window === 'undefined' ? globalThis : window);
