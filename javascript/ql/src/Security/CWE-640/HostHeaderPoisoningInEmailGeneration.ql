/**
 * @name Host header poisoning in email generation
 * @description Using the HTTP Host header to construct a link in an email can facilitate phishing
 *              attacks and leak password reset tokens.
 * @kind path-problem
 * @problem.severity error
 * @precision high
 * @id js/host-header-forgery-in-email-generation
 * @tags security
 *       external/cwe/cwe-640
 */

import javascript
import semmle.javascript.security.dataflow.HostHeaderPoisoningInEmailGeneration::HostHeaderPoisoningInEmailGeneration
import DataFlow::PathGraph

from Configuration cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasPathFlow(source, sink)
select sink.getNode(), "Links in this email can be hijacked by poisoning the HTTP host header $@.", source, "here"
