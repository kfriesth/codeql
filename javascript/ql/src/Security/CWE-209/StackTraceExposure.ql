/**
 * @name Information exposure through a stack trace
 * @description Propagating stack trace information to an external user can
 *              unintentionally reveal implementation details that are useful
 *              to an attacker for developing a subsequent exploit.
 * @kind path-problem
 * @problem.severity warning
 * @precision very-high
 * @id js/stack-trace-exposure
 * @tags security
 *       external/cwe/cwe-209
 */

import javascript
import semmle.javascript.security.dataflow.StackTraceExposure::StackTraceExposure
import DataFlow::PathGraph

from Configuration cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasPathFlow(source, sink)
select sink.getNode(), "Stack trace information from $@ may be exposed to an external user here.",
       source, "here"
