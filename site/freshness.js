(function (root) {
  function assessFreshness(data, calendar, now = new Date()) {
    const today = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    const available = calendar && today <= calendar.valid_until;
    const completed = available ? calendar.closes.filter(item => Date.parse(item.close) <= now.getTime()) : [];
    const required = completed.at(-1)?.date || null;
    const captureAge = now.getTime() - Date.parse(data.account?.observed_at || '');
    const accountFresh = data.account?.valuation_date === required && captureAge >= 0 && captureAge <= 86400000;
    const modelFresh = Boolean(required) && data.authority?.status === 'passed' && data.freshness?.data_end === required;
    return {required, modelFresh, accountFresh, isFresh:modelFresh && accountFresh};
  }
  root.assessFreshness = assessFreshness;
  if (typeof module !== 'undefined') module.exports = {assessFreshness};
})(typeof window === 'undefined' ? globalThis : window);
