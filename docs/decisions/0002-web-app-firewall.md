# Use BunkerWeb as a Web Application Firewall

## Context and Problem Statement

- We can use a vanilla web server like Nginx or Apache.
- However, Web Application Firewall (WAF) solutions contain many additional
  security features.
- They require less configuration than setting this up and maintaining it
  ourselves, so make sense to leverage for better general security.
- We can have built in Brotli compression, DDOS protection, modsecurity rules,
  'bad behaviour' and bot blocking all included.

## Considered Options

- Vanilla Nginx + ModSecurity rules
- Safeline
- BunkerWeb
- openappsec
- OWASP Coraza

## Decision Outcome

- Vanilla ModSecurity is to much maintenance hassle.
- Safeline is paid for most of the good features (freemium).
- openappsec isn't well supported and we have uncertainties around the
  ML-based approach used here (an precedence for prod use?)
- OWASP Coraza is no doubt fantastic - officially supported by OWASP -
  but the issue is integration into our app. There is no clear pathway
  yet outside of integrating into a Golang app. Integrating into Caddy
  is possible, but Nginx is likely better.

We chose BunkerWeb as it integrates OWASP ModSecurity rulesets, is based
on standard Nginx, and is quite configurable. The code is also fully
open-source and community driven. It seems like a safe bet.

### Consequences

- Good, because it's based on Nginx upstream code.
- Good, because it integrates OWASP best practice ModSecurity rules.
- Good, because it's easy to replace our existing Nginx setup.
- Bad, because it's not an officially supported OWASP project.
- Good, the model is a generous freemium one, that could change in future
  (the code is all open, however).
- Good, because migration away should be relatively easy if needed.
- Good, because OpenAppSec may be integrated in future:
  <https://github.com/bunkerity/bunkerweb/issues/819>
- Bad, because we don't have great benchmark comparisons (but it's
  based on Nginx, so shouldn't be an issue).
- Bad, because we don't have good clarity on it's usage in production
  in the wild.
