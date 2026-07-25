# Security Policy

## Supported versions

conlangkit is pre-1.0. Security fixes ship from the latest `main` and the most
recent release on PyPI.

## Reporting a vulnerability

Please report suspected vulnerabilities privately using GitHub's
[private vulnerability reporting](https://github.com/dhh1128/conlangkit/security/advisories/new)
("Report a vulnerability" under the repository's **Security** tab). Do not open a
public issue for a security problem.

You can expect an acknowledgement within **3 business days**. We aim to have a
fix or a documented mitigation within **30 days**, coordinating a disclosure
timeline with you. There is no bug-bounty program.

## Scope

conlangkit reads and writes glossary/language files and shells out to NLTK data.
Reports about parsing untrusted glossary input, path handling, or dependency
supply-chain issues are in scope.
