# Retire the legacy work-management platform

**Synthetic enterprise evidence and modeled results.**

Result: **ESTABLISHED_BLOCKERS**

Modeled consequence of declared architecture. Metadata compatibility is not operational verification; this result does not authorize cutover.

Snapshot: `323ba0c95a5369f202bce18fc210d0b3fe84c7977f8fa0c767a00a1ddbad750b`  
Assessment: `09cbef7ce86af0f8f44be4205d246c29db91e68379131ddee7030a983a33c374`

## Requirement consequences

| Requirement | Before | Proposed | Interpretation |
|---|---|---|---|
| Attribute webinar outcomes (attribution) | SUPPORTED | UNSUPPORTED | established blocker |
| Create shared campaign (campaign-creation) | SUPPORTED | UNSUPPORTED | established blocker |
| Approve campaign content (content-approval) | SUPPORTED | SUPPORTED | supported in declared model |
| Send webinar follow-up (follow-up) | SUPPORTED | UNSUPPORTED | established blocker |
| Route qualified leads (lead-routing) | SUPPORTED | SUPPORTED | supported in declared model |
| Deliver approved messages (messaging) | SUPPORTED | SUPPORTED | supported in declared model |
| Analyze product engagement (product-insight) | SUPPORTED | SUPPORTED | supported in declared model |
| Register webinar participant (registration) | SUPPORTED | SUPPORTED | supported in declared model |
| Report operational outcomes (reporting) | SUPPORTED | SUPPORTED | supported in declared model |
| Launch annual seasonal campaign (seasonal) | UNKNOWN | UNKNOWN | unresolved / conditional |
| Establish webinar campaign identifiers (webinar-identifiers) | SUPPORTED | UNSUPPORTED | established blocker |
| Publish website (website) | SUPPORTED | SUPPORTED | supported in declared model |

## Witness branches

Dependency paths run from the business requirement toward its provider. Evidence IDs resolve in [evidence-index.json](evidence-index.json). Proposal references are proposed future assertions, not observed source evidence.

### attribution

- req:attribution [UNSUPPORTED] → dependency:attribution:0 [UNSUPPORTED] → req:webinar-identifiers [UNSUPPORTED] → dependency:webinar-identifiers:0 [UNSUPPORTED] → req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:0 [UNSUPPORTED] → sys:work-manager [UNSUPPORTED]
  Evidence: `1a6778b367f77493eadcabc3dcfd80559cdc7a83b82dc5a63fa11e031a8f114c`, `28c1e5af740f3649f21256886da661690a1dde1f86cac2482eed60883878c947`, `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `a6b20bce72df26a32e3618f8e47fa89be72ab5958834c470eeb0c0aa3fbbd125`, `ccd9ed7dfd1f26e46cb11c6de539a7d120e535f27ec85f040ad26ac863f2a193`, `fe1459e51326c59890390c8aee59d65e013d8336b3a321eae816d3c861679a6d`, `proposal:1d9f6eae1af685b7db95326c5c355cb4930be95196a90d5e9cb4e81b293c58d3:0`
- req:attribution [UNSUPPORTED] → dependency:attribution:0 [UNSUPPORTED] → req:webinar-identifiers [UNSUPPORTED] → dependency:webinar-identifiers:0 [UNSUPPORTED] → req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:1 [UNSUPPORTED] → int:brief-status [UNSUPPORTED]
  Evidence: `1a6778b367f77493eadcabc3dcfd80559cdc7a83b82dc5a63fa11e031a8f114c`, `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `567fd9201cf8fc23614642f90283daa54e468300c4a4de4366a52ba031b25050`, `a6b20bce72df26a32e3618f8e47fa89be72ab5958834c470eeb0c0aa3fbbd125`, `ccd9ed7dfd1f26e46cb11c6de539a7d120e535f27ec85f040ad26ac863f2a193`, `d7ad6881f42442c71734d38503fa245e92f170d2043dc59ae868e1e94c157572`, `fe1459e51326c59890390c8aee59d65e013d8336b3a321eae816d3c861679a6d`

### campaign-creation

- req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:0 [UNSUPPORTED] → sys:work-manager [UNSUPPORTED]
  Evidence: `28c1e5af740f3649f21256886da661690a1dde1f86cac2482eed60883878c947`, `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `proposal:1d9f6eae1af685b7db95326c5c355cb4930be95196a90d5e9cb4e81b293c58d3:0`
- req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:1 [UNSUPPORTED] → int:brief-status [UNSUPPORTED]
  Evidence: `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `567fd9201cf8fc23614642f90283daa54e468300c4a4de4366a52ba031b25050`, `d7ad6881f42442c71734d38503fa245e92f170d2043dc59ae868e1e94c157572`

### content-approval

- req:content-approval [SUPPORTED] → dependency:content-approval:0 [SUPPORTED] → sys:content-review [SUPPORTED]
  Evidence: `77b9199159fd342377b5878e93618989aa0503d23c21e45db1dfb252e658fe56`, `7ae063d55a04996ee33837282e21a185ad1d65f7a94988169ce128ab16b84e70`, `7c9caaed966729860376bc6560c2c8c79182b6a9e7f23843a5f34a23ebe77c90`

### follow-up

- req:follow-up [UNSUPPORTED] → dependency:follow-up:0 [UNSUPPORTED] → req:webinar-identifiers [UNSUPPORTED] → dependency:webinar-identifiers:0 [UNSUPPORTED] → req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:0 [UNSUPPORTED] → sys:work-manager [UNSUPPORTED]
  Evidence: `1451d58efb3597172ee3a4440577381f2014ce0b0e973219e7c947b02447805d`, `28c1e5af740f3649f21256886da661690a1dde1f86cac2482eed60883878c947`, `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `6b02dd85cee861fdd7a52a02eaa00c6e676c40875046b4659250f8ff81dce26d`, `a6b20bce72df26a32e3618f8e47fa89be72ab5958834c470eeb0c0aa3fbbd125`, `fe1459e51326c59890390c8aee59d65e013d8336b3a321eae816d3c861679a6d`, `proposal:1d9f6eae1af685b7db95326c5c355cb4930be95196a90d5e9cb4e81b293c58d3:0`
- req:follow-up [UNSUPPORTED] → dependency:follow-up:0 [UNSUPPORTED] → req:webinar-identifiers [UNSUPPORTED] → dependency:webinar-identifiers:0 [UNSUPPORTED] → req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:1 [UNSUPPORTED] → int:brief-status [UNSUPPORTED]
  Evidence: `1451d58efb3597172ee3a4440577381f2014ce0b0e973219e7c947b02447805d`, `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `567fd9201cf8fc23614642f90283daa54e468300c4a4de4366a52ba031b25050`, `6b02dd85cee861fdd7a52a02eaa00c6e676c40875046b4659250f8ff81dce26d`, `a6b20bce72df26a32e3618f8e47fa89be72ab5958834c470eeb0c0aa3fbbd125`, `d7ad6881f42442c71734d38503fa245e92f170d2043dc59ae868e1e94c157572`, `fe1459e51326c59890390c8aee59d65e013d8336b3a321eae816d3c861679a6d`

### lead-routing

- req:lead-routing [SUPPORTED] → dependency:lead-routing:0 [SUPPORTED] → sys:crm [SUPPORTED]
  Evidence: `94c6411ad046f2eeb43fd6d1d85c1569ddbdfff8d991bb93839f643873a0a666`, `9a456bd4b521f80c9da69a8b811a296d14c492f8044acb5c0da5ba5f36e0a8ab`, `eb7860d9e00779a4fe26bfd81dcd80402c7545b924b85555572767861c5dddaa`
- req:lead-routing [SUPPORTED] → dependency:lead-routing:1 [SUPPORTED] → sys:automation [SUPPORTED]
  Evidence: `72f8d1813420db744386695931874b7d884e527ef02a8707bfc79f3faeb1f7b8`, `94c6411ad046f2eeb43fd6d1d85c1569ddbdfff8d991bb93839f643873a0a666`, `b2bd4b48683fbdcad776163a4e2aa8f5c444b1eb48c74eab433ea67991288d4d`

### messaging

- req:messaging [SUPPORTED] → dependency:messaging:0 [SUPPORTED] → sys:email [SUPPORTED]
  Evidence: `32efb91712ccc3d2978d9261d9a016514bd8559bd7965d25e4261e8f1a23f6f1`, `9cefb7d63d49903cd58593c95cf94029c29f9dce14303b8bbb5dd888ebedf8e9`, `fd67e645732fd2f7d9ca14432cf624501531e66a22c60ccf744ce5b0c1843289`
- req:messaging [SUPPORTED] → dependency:messaging:1 [SUPPORTED] → sys:automation [SUPPORTED]
  Evidence: `b2bd4b48683fbdcad776163a4e2aa8f5c444b1eb48c74eab433ea67991288d4d`, `e2275762ab2eb50b735aa8c7c6041d4d73b2c11b4fd78c0bbd203048f040f960`, `fd67e645732fd2f7d9ca14432cf624501531e66a22c60ccf744ce5b0c1843289`

### product-insight

- req:product-insight [SUPPORTED] → dependency:product-insight:0 [SUPPORTED] → sys:collector [SUPPORTED]
  Evidence: `42d000a32d5747653be5c610b2f7ad18b0253f17aa92e2cbd1d466117c318862`, `8a91fa66eca6e38896bd7862f7271b45615b5da99d1477a56f862a5582caa2f9`, `d8d0e13a14c977e9d0d8bc5caa015374cf09bf9a4e784ccc02da667fc4bef309`
- req:product-insight [SUPPORTED] → dependency:product-insight:1 [SUPPORTED] → sys:warehouse [SUPPORTED]
  Evidence: `9a15f36d62336c0466398ce4e2fc3cb5969f18696ecb42d51920c37a426660f8`, `a2f6e7fedc16f858c24a5b46b160e997ac9fba72952eea7bdb46a94b152ffdc2`, `c8402950e95755e117f9691d9016bc5cfec5463c07f56d318f1528f571aa3ae9`, `d8d0e13a14c977e9d0d8bc5caa015374cf09bf9a4e784ccc02da667fc4bef309`

### registration

- req:registration [SUPPORTED] → dependency:registration:0 [SUPPORTED] → sys:registration [SUPPORTED]
  Evidence: `d70372d2ca5a87ebe7730646d34b05cba6faa494ac71cda6b794dc85767c58c0`, `e83e4355979bf9fd2edbe226a602b1b5cbc42400b26a010932d6e834c11432ab`, `f880ce26d7bc44200d5734ae26a91414e9cfb51d6d4591e09bf69fc3827f8a74`
- req:registration [SUPPORTED] → dependency:registration:1 [SUPPORTED] → sys:webinar [SUPPORTED]
  Evidence: `808f052a74d5ac5ed8d07fe5252201bce2f1a72d8ee98848eddc3b98883a853a`, `a3fbf816f5181bb629fabcf67ec3d53ae9dec6fb67baaa93545d2c49e28a71ba`, `e83e4355979bf9fd2edbe226a602b1b5cbc42400b26a010932d6e834c11432ab`, `f6e7b23029eb64bb61b67d1f84d3fbda092f04327e7aab253f8dc76a8527aef7`

### reporting

- req:reporting [SUPPORTED] → dependency:reporting:0 [SUPPORTED] → sys:bi [SUPPORTED]
  Evidence: `68e1e071141abec6859ad792962076191977aa235de64c1b1a88156642cebef6`, `869222b3ad03ccc22a36871eacd3eedf71fc1f3c6c6837d30b7df514b03ebb03`, `ce727ea538fc11ca8218d5397781e8d455fabac6c989cbeac4bf0b930b7e9965`
- req:reporting [SUPPORTED] → dependency:reporting:1 [SUPPORTED] → sys:warehouse [SUPPORTED]
  Evidence: `68e1e071141abec6859ad792962076191977aa235de64c1b1a88156642cebef6`, `8a6bc8fead01f830ed344893b1a048d332dec5a7313dabafdd8ebe7c54d617b7`, `9a15f36d62336c0466398ce4e2fc3cb5969f18696ecb42d51920c37a426660f8`

### seasonal

- req:seasonal [UNKNOWN] → dependency:seasonal:0 [UNKNOWN]
  Evidence: `3d75a8ce55ecb5af19ae28666759be1944d65c284d1f297d5af1b5bee026b829`, `4242a8a736a7a3ee2e444501d6b70156235233e823231513871b795b8b970faf`, `e543fee3380ba7146f5e1a54cdb5cf6d2d925136428fb77dcc8dfde48d22e90c`

### webinar-identifiers

- req:webinar-identifiers [UNSUPPORTED] → dependency:webinar-identifiers:0 [UNSUPPORTED] → req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:0 [UNSUPPORTED] → sys:work-manager [UNSUPPORTED]
  Evidence: `28c1e5af740f3649f21256886da661690a1dde1f86cac2482eed60883878c947`, `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `a6b20bce72df26a32e3618f8e47fa89be72ab5958834c470eeb0c0aa3fbbd125`, `fe1459e51326c59890390c8aee59d65e013d8336b3a321eae816d3c861679a6d`, `proposal:1d9f6eae1af685b7db95326c5c355cb4930be95196a90d5e9cb4e81b293c58d3:0`
- req:webinar-identifiers [UNSUPPORTED] → dependency:webinar-identifiers:0 [UNSUPPORTED] → req:campaign-creation [UNSUPPORTED] → dependency:campaign-creation:1 [UNSUPPORTED] → int:brief-status [UNSUPPORTED]
  Evidence: `52f00bed3eb9997b17c4e5f214c0b2e3cecf94626e8136604b18f7ec38d2ff9b`, `567fd9201cf8fc23614642f90283daa54e468300c4a4de4366a52ba031b25050`, `a6b20bce72df26a32e3618f8e47fa89be72ab5958834c470eeb0c0aa3fbbd125`, `d7ad6881f42442c71734d38503fa245e92f170d2043dc59ae868e1e94c157572`, `fe1459e51326c59890390c8aee59d65e013d8336b3a321eae816d3c861679a6d`

### website

- req:website [SUPPORTED] → dependency:website:0 [SUPPORTED] → sys:cms [SUPPORTED]
  Evidence: `48796ca631813b8d22e76db19b9a190f4d1ba1d97dd4574a940ff179934c64f0`, `87d3587866352b67cd8b8274140c9799afc739d2f8507e01570143c201e685be`, `f65e3d84261aa16a752c652bea05281f7d5a17140df34b8f65ef9b3079f0f9af`
- req:website [SUPPORTED] → dependency:website:1 [SUPPORTED] → sys:dam [SUPPORTED]
  Evidence: `573de469d5e14047f64f6470f9ac011abd9e5b776a101fcbdfcbc8e20175cc39`, `87d3587866352b67cd8b8274140c9799afc739d2f8507e01570143c201e685be`, `f1b142ade0cbe2b0244fae7789ecc9e77c187d95c5af441af4ef55de83bc5a75`

## Residual references

- dependency:campaign-creation:0: SUPPORTED; still references work-manager
- dependency:reporting:2: SUPPORTED; still references work-manager
- dependency:seasonal:0: UNKNOWN; still references work-manager
- integration:brief-status: SUPPORTED; still references work-manager
- integration:campaign-approval: SUPPORTED; still references work-manager
- integration:campaign-reporting: SUPPORTED; still references work-manager
- integration:seasonal-launch: SUPPORTED; still references work-manager

Proposed relationship issues: []

## Coverage and unresolved evidence

Consequences detected outside the selected requirement scope: {}

- work-manager: UNKNOWN. review:work-manager: exclusions or missing reviewer; review:work-manager: expected export missing; review:work-manager: partial collection; review:work-manager: partial observation period Evidence: review:work-manager

Unresolved estate facts (includes facts outside this proposal's requirement scope): dependency:seasonal:0, integration:legacy-personalization, ownership:work-manager

## Activity prerequisites

Planned order: none

Cycle members: approve-cutover, remove-legacy

Missing prerequisites: {}

Missing acceptance evidence: {&#x27;remove-legacy&#x27;: [&#x27;operational-acceptance&#x27;]}

Ready to progress now: none

Architecture feasibility and execution readiness are separate. Uncompleted acceptance gates remain even when declared interface gaps are closed.
