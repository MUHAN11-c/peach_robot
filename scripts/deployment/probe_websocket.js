// Read only: the deployment exposes projections, not arbitrary ROS topics.
const fs = require('fs');
const report = {topic: '/peach_observability/web_state', frames: []};
const ws = new WebSocket('ws://127.0.0.1:9090');
let done = false;
const timer = setTimeout(() => finish('web_state timeout'), 15000);
function finish(error) {
  if (done) return;
  done = true;
  clearTimeout(timer);
  report.passed = !error;
  if (error) report.error = String(error);
  if (ws.readyState === 1) {
    ws.send(JSON.stringify({op: 'unsubscribe', topic: report.topic, id: 'deployment-state'}));
  }
  ws.close();
  fs.writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
  process.exitCode = error ? 1 : 0;
}
ws.addEventListener('open', () => ws.send(JSON.stringify({
  op: 'subscribe', topic: report.topic, type: 'std_msgs/msg/String',
  id: 'deployment-state', queue_length: 1,
})));
ws.addEventListener('error', () => finish('WebSocket connection failed'));
ws.addEventListener('message', event => {
  try {
    const data = JSON.parse(String(event.data));
    if (data.op !== 'publish' || data.topic !== report.topic) return;
    const state = JSON.parse(data.msg.data);
    const facts = state.startup?.facts;
    const task = state.task_executor?.state;
    if (facts?.hardware_mode !== 'mock' || !task ||
        !['execution_enabled', 'grasp_enabled', 'tool_enabled', 'action_active']
          .every(key => task[key] === false)) {
      return finish('mock identity or disabled enable readback failed');
    }
    report.frames.push({received_ms: Date.now(), hardware_mode: facts.hardware_mode,
      state_seq: task.state_seq, execution: task.execution_enabled,
      grasp: task.grasp_enabled, tool: task.tool_enabled});
    if (report.frames.length >= 2) finish();
  } catch (error) {
    finish(error.message);
  }
});
