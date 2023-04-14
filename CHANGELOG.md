# Changelog

<!-- insertion marker -->
## Unreleased

<small>[Compare with latest](https://github.com/QUT-Digital-Observatory/youte/compare/v2.1.0...HEAD)</small>

<!-- insertion marker -->
## [v2.1.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/v2.1.0) - 2023-04-14

<small>[Compare with 2.0.1](https://github.com/QUT-Digital-Observatory/youte/compare/2.0.1...v2.1.0)</small>

### Added

- add black to isort ([8d1f42c](https://github.com/QUT-Digital-Observatory/youte/commit/8d1f42c447bf6d5a5fa79b270b9507900658f078) by Boyd Nguyen).
- add missing video attributes ([5fdf71e](https://github.com/QUT-Digital-Observatory/youte/commit/5fdf71e3b9fdc15782d7b2037972c781b61424a8) by Boyd Nguyen).
- add v2.0.2 ([8f900d3](https://github.com/QUT-Digital-Observatory/youte/commit/8f900d32bd4e97a18cd95aa4a118773da25f17d9) by Boyd Nguyen).
- add python semantic release + bump version ([999430b](https://github.com/QUT-Digital-Observatory/youte/commit/999430baf901699ee4e765fdf256041611e5541a) by Boyd Nguyen).
- add database + full archive function WIP ([019457c](https://github.com/QUT-Digital-Observatory/youte/commit/019457c5b19ef4565130327e34bd2563b08723d6) by Boyd Nguyen).
- add changelog ([e815753](https://github.com/QUT-Digital-Observatory/youte/commit/e8157533e04c4111aa031f2ac14f2e715ed6c5bf) by Boyd Nguyen).

### Fixed

- fix option name for logging verbosity ([1ebaf17](https://github.com/QUT-Digital-Observatory/youte/commit/1ebaf1718f1143cae08ecd72eebfb9b26047a492) by Boyd Nguyen).
- fix: improve logging ([66a7b68](https://github.com/QUT-Digital-Observatory/youte/commit/66a7b68a4e77c34a05e0f4208fe62a00b9bd3182) by Boyd Nguyen).
- fix(parser): use dict.get() to allow for nullable fields when parsing JSON ([3a2e8c9](https://github.com/QUT-Digital-Observatory/youte/commit/3a2e8c9db35639b31c1911da8b3d4b6905725802) by Boyd Nguyen).
- fix(collector): avoid inputting error messages to output file ([4a186dc](https://github.com/QUT-Digital-Observatory/youte/commit/4a186dc2b91f2d859439e773dd1a2ec62c1e4af6) by Boyd Nguyen).
- fix(resources): refine resource schema + make optional fields optional ([821bca9](https://github.com/QUT-Digital-Observatory/youte/commit/821bca98e1c237bffe90cb3f3356cefc74ab8987) by Boyd Nguyen).
- fix(parser): fix KeyError in parse_video + parse_videos ([05ade72](https://github.com/QUT-Digital-Observatory/youte/commit/05ade72ddd7ce644b573069434db275fac105f98) by Boyd Nguyen).

### Removed

- remove redundant package ([8594d4e](https://github.com/QUT-Digital-Observatory/youte/commit/8594d4e8ca237b5a74c189f823a631abedbfa4b0) by Boyd Nguyen).

## [2.0.1](https://github.com/QUT-Digital-Observatory/youte/releases/tag/2.0.1) - 2023-03-20

<small>[Compare with 2.0.0](https://github.com/QUT-Digital-Observatory/youte/compare/2.0.0...2.0.1)</small>

### Added

- add mkdocstring ([66beaa2](https://github.com/QUT-Digital-Observatory/youte/commit/66beaa27f5850063faed54ba016855eb5eb7e9d2) by Boyd Nguyen).
- add mkdocs-docstring for API reference ([1734a25](https://github.com/QUT-Digital-Observatory/youte/commit/1734a25005ea2e80d4e5492d68de0f1386e19ec3) by Boyd Nguyen).
- add API reference ([eb97348](https://github.com/QUT-Digital-Observatory/youte/commit/eb97348f30e8f764dc06330d6086d973ae0d201f) by Boyd Nguyen).

### Fixed

- fix youte install ([42b508f](https://github.com/QUT-Digital-Observatory/youte/commit/42b508f78de971b3bdc0773df3bf8551f14ec849) by Boyd Nguyen).
- fix requirements for mkdocs ([c3ec2a9](https://github.com/QUT-Digital-Observatory/youte/commit/c3ec2a99b26e2a7b803e00f95b48fce63268e0f8) by Boyd Nguyen).

### Changed

- change version to 2.0.1 ([d82c8c4](https://github.com/QUT-Digital-Observatory/youte/commit/d82c8c4ff3aef119caae464198fe0d8c531b9add) by Boyd Nguyen).
- change docstring style to google ([b8c3ae8](https://github.com/QUT-Digital-Observatory/youte/commit/b8c3ae82cdab49b9bb6f382aa71e06d06d5ac8ef) by Boyd Nguyen).

## [2.0.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/2.0.0) - 2023-03-16

<small>[Compare with 1.3.0](https://github.com/QUT-Digital-Observatory/youte/compare/1.3.0...2.0.0)</small>

### Added

- add related-to docs ([11e8fe3](https://github.com/QUT-Digital-Observatory/youte/commit/11e8fe33f9b49405076a233bb19a367ca24d1fe9) by Boyd Nguyen).

## [1.3.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/1.3.0) - 2023-02-24

<small>[Compare with 1.2.0](https://github.com/QUT-Digital-Observatory/youte/compare/1.2.0...1.3.0)</small>

### Added

- add output flag ([040ac78](https://github.com/QUT-Digital-Observatory/youte/commit/040ac78a6577d04461e8b898b3527b99bd5c9f0f) by Boyd Nguyen).
- add region and language filter to search ([32451c7](https://github.com/QUT-Digital-Observatory/youte/commit/32451c736f9d8c70918ae707baff237680eb2827) by Boyd Nguyen).
- add feedback is welcome! paragraph ([ac1aa87](https://github.com/QUT-Digital-Observatory/youte/commit/ac1aa872c97d35c4748bad9edd46a4c956dcba9b) by Boyd Nguyen).
- add logos and screenshots ([fa2e726](https://github.com/QUT-Digital-Observatory/youte/commit/fa2e726304db4d66ff48d3b881bd5d257e8fddb8) by Boyd Nguyen).
- add code formatting extensions ([9514b0f](https://github.com/QUT-Digital-Observatory/youte/commit/9514b0f6605ef4777d3278f5e1ca9ed52b99846b) by Boyd Nguyen).
- add python ver ([84a4ca2](https://github.com/QUT-Digital-Observatory/youte/commit/84a4ca28186d981e4dc4e1e04da908fef6737b90) by Boyd Nguyen).
- add yaml ([adca2f5](https://github.com/QUT-Digital-Observatory/youte/commit/adca2f55b377917a0fc8c0cb69e53f5e26b869e9) by Boyd Nguyen).
- add docs ([42a1457](https://github.com/QUT-Digital-Observatory/youte/commit/42a1457350987bfa80eabee73b6a3616b91edf4c) by Boyd Nguyen).

### Fixed

- fix typo ([7705b7c](https://github.com/QUT-Digital-Observatory/youte/commit/7705b7cc8a738d98a6978563f0e08ca37bdc6256) by Boyd Nguyen).

### Changed

- change help text for output ([4ce4321](https://github.com/QUT-Digital-Observatory/youte/commit/4ce4321ac161d7f6ee3b7a22de399ba589229c2f) by Boyd Nguyen).
- change entry point ([7df3150](https://github.com/QUT-Digital-Observatory/youte/commit/7df3150b5c533b625c16ea5311f2bbb31586edff) by Boyd Nguyen).
- change palette and heading style ([513733f](https://github.com/QUT-Digital-Observatory/youte/commit/513733f319d96388ec2ecc4c090feb029e0de3d1) by Boyd Nguyen).

### Removed

- remove plugins ([be5c20f](https://github.com/QUT-Digital-Observatory/youte/commit/be5c20f97dad61a09f54b03043e8885aadbc34bb) by Boyd Nguyen).
- remove db overwrite check + add ability to tidy multiple json at once ([fe88a1b](https://github.com/QUT-Digital-Observatory/youte/commit/fe88a1be0d36d115f30909530b06f79ab18c42af) by Boyd Nguyen).

## [1.2.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/1.2.0) - 2023-02-07

<small>[Compare with 1.1.0](https://github.com/QUT-Digital-Observatory/youte/compare/1.1.0...1.2.0)</small>

### Added

- add limit argument to search ([0cb1df4](https://github.com/QUT-Digital-Observatory/youte/commit/0cb1df46cc45c9cacf0cc264a3ee3c16b5346c92) by Boyd Nguyen).

## [1.1.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/1.1.0) - 2022-12-06

<small>[Compare with 1.0.1](https://github.com/QUT-Digital-Observatory/youte/compare/1.0.1...1.1.0)</small>

### Added

- add most-popular command ([44103cf](https://github.com/QUT-Digital-Observatory/youte/commit/44103cfb64ce3652f7f49f0d46fb52841de1409b) by Boyd Nguyen).
- add docs and fix typos in function docs ([cac9196](https://github.com/QUT-Digital-Observatory/youte/commit/cac9196a8f4c903bef480b2467995604dd616a7b) by Boyd Nguyen).

## [1.0.1](https://github.com/QUT-Digital-Observatory/youte/releases/tag/1.0.1) - 2022-12-01

<small>[Compare with 1.0.0](https://github.com/QUT-Digital-Observatory/youte/compare/1.0.0...1.0.1)</small>

### Added

- add test for get-related command ([5fb2533](https://github.com/QUT-Digital-Observatory/youte/commit/5fb253341d3dcde7923396f9f2543bb461ea36c4) by Boyd Nguyen).
- add get-related command to retrieve related videos ([03ee4ba](https://github.com/QUT-Digital-Observatory/youte/commit/03ee4ba914aa845616f2a894864cbdce2077a632) by Boyd Nguyen).

### Removed

- remove query argument in search() method ([c92c6df](https://github.com/QUT-Digital-Observatory/youte/commit/c92c6df77ecb6df54e1c58d578f6e29e26dc1757) by Boyd Nguyen).

## [1.0.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/1.0.0) - 2022-11-23

<small>[Compare with 0.1.1](https://github.com/QUT-Digital-Observatory/youte/compare/0.1.1...1.0.0)</small>

### Added

- add testing session ([6a02c55](https://github.com/QUT-Digital-Observatory/youte/commit/6a02c55d3f164a20fe15e4cc681cedc9ba152b37) by Boyd Nguyen).
- add error handling for dehydrate ([1c26ad0](https://github.com/QUT-Digital-Observatory/youte/commit/1c26ad03d71606af92e4f4c35dade538be766f29) by Boyd Nguyen).
- add versioning ([4fc973f](https://github.com/QUT-Digital-Observatory/youte/commit/4fc973f1b17d3c738acdf33a4b452d1aae29e6a0) by Boyd Nguyen).
- add channel mapping ([89426c0](https://github.com/QUT-Digital-Observatory/youte/commit/89426c0272a9cd2435a76554a0dd49c34e9fd9ba) by Boyd Nguyen).
- add dehydrate command ([9030a24](https://github.com/QUT-Digital-Observatory/youte/commit/9030a24498ae7d4d531b81ef1fea37c08c067d08) by Boyd Nguyen).
- add search options + export to csv + list history command ([3dcbfd0](https://github.com/QUT-Digital-Observatory/youte/commit/3dcbfd015ab503dbdafc0cea8d8e5705956ddd20) by Boyd Nguyen).
- add csv export ([7bb6930](https://github.com/QUT-Digital-Observatory/youte/commit/7bb693018a4de798e2e56b878bab32b3f4196f9d) by Boyd Nguyen).
- add type to search ([afb03e0](https://github.com/QUT-Digital-Observatory/youte/commit/afb03e071b5ae57960a05ba032b1ace555d91a2b) by Boyd Nguyen).
- add options to search command ([bc7f7a7](https://github.com/QUT-Digital-Observatory/youte/commit/bc7f7a7b6acb7295ae9fdaecfc7b003743320ccd) by Boyd Nguyen).

### Fixed

- fix typo in function docs ([bcb0b22](https://github.com/QUT-Digital-Observatory/youte/commit/bcb0b22fc1a096027a583f19ff324b2a0a79192d) by Boyd Nguyen).
- fix removal of db before search finishes ([2b8eb88](https://github.com/QUT-Digital-Observatory/youte/commit/2b8eb88dd6ac4d4769ebf79d838bf4ac940a86f7) by Boyd Nguyen).

### Changed

- changed version ([4e1669d](https://github.com/QUT-Digital-Observatory/youte/commit/4e1669deb9f10bea9a3f4c1d695e29c7fe762cd6) by Boyd Nguyen).
- change youtupy to youte ([c242e61](https://github.com/QUT-Digital-Observatory/youte/commit/c242e6183dab5297f584ace77175dad709d7c641) by Boyd Nguyen).
- change hydrate + list-comments to yield response ([1d228bd](https://github.com/QUT-Digital-Observatory/youte/commit/1d228bdd8de5c80cf02a2c785f30d38083ec6d6c) by Boyd Nguyen).
- change search_result schema ([7c936f8](https://github.com/QUT-Digital-Observatory/youte/commit/7c936f8675406d1600ba517409b1e9ebec26b1b8) by Boyd Nguyen).

### Removed

- remove quota + yield json instead of writing to outfile ([fcdf970](https://github.com/QUT-Digital-Observatory/youte/commit/fcdf970edbf96d3ded51b5e73316106b62eb96dd) by Boyd Nguyen).

## [0.1.1](https://github.com/QUT-Digital-Observatory/youte/releases/tag/0.1.1) - 2022-10-10

<small>[Compare with 0.1.0](https://github.com/QUT-Digital-Observatory/youte/compare/0.1.0...0.1.1)</small>

### Added

- add \n to search arguments doc ([15c3966](https://github.com/QUT-Digital-Observatory/youte/commit/15c3966024bbb0bce39ff88bc90cc30a8ee15c62) by Boyd Nguyen).
- add click validation callback for date format ([451f963](https://github.com/QUT-Digital-Observatory/youte/commit/451f96373f8a06731952d2056c215589cb92a387) by Boyd Nguyen).

## [0.1.0](https://github.com/QUT-Digital-Observatory/youte/releases/tag/0.1.0) - 2022-09-21

<small>[Compare with 0.0.2](https://github.com/QUT-Digital-Observatory/youte/compare/0.0.2...0.1.0)</small>

### Added

- add db schemas ([5516020](https://github.com/QUT-Digital-Observatory/youte/commit/55160205a168feb513ab0d03456e7d5fa177fbe6) by Boyd Nguyen).
- add messaging on outfile and schema ([58a9de5](https://github.com/QUT-Digital-Observatory/youte/commit/58a9de537953da5fbdf108f0c81da48c56eb9566) by Boyd Nguyen).
- add messaing about search outfile ([502652b](https://github.com/QUT-Digital-Observatory/youte/commit/502652bc4df8aecd6095cf7e2b240e4737021455) by Boyd Nguyen).

### Changed

- changed version to 0.1.0 ([1ca612c](https://github.com/QUT-Digital-Observatory/youte/commit/1ca612c2ce5d00975ea6dc6cdab989bea26a9443) by Boyd Nguyen).

## [0.0.2](https://github.com/QUT-Digital-Observatory/youte/releases/tag/0.0.2) - 2022-09-07

<small>[Compare with 0.0.1b](https://github.com/QUT-Digital-Observatory/youte/compare/0.0.1b...0.0.2)</small>

### Fixed

- fix db commit error ([8dbec23](https://github.com/QUT-Digital-Observatory/youte/commit/8dbec2323b9444da19f3746292bd64509dd5b994) by Boyd Nguyen).

### Changed

- changed version ([fd20e33](https://github.com/QUT-Digital-Observatory/youte/commit/fd20e33ab5d8e8e4f379cc2a907f73ce925a5392) by Boyd Nguyen).

### Removed

- remove trailing period from url ([fde21b7](https://github.com/QUT-Digital-Observatory/youte/commit/fde21b70df46fc91a913f13593a3d856664a5ded) by Jonathan Gray).

## [0.0.1b](https://github.com/QUT-Digital-Observatory/youte/releases/tag/0.0.1b) - 2022-09-02

<small>[Compare with first commit](https://github.com/QUT-Digital-Observatory/youte/compare/4562a2b20cdd68e305a4b51ebba3b02ba132665b...0.0.1b)</small>

### Added

- additional params for search command ([e19eb2c](https://github.com/QUT-Digital-Observatory/youte/commit/e19eb2c5eade9736b3151efe5c876565578fcf28) by Boyd Nguyen).
- add config delete profile ([08430d0](https://github.com/QUT-Digital-Observatory/youte/commit/08430d08cf7afb977ee7298377cb838fd49697e8) by Boyd Nguyen).
- Added notes about file types and time zone ([a4ba7ce](https://github.com/QUT-Digital-Observatory/youte/commit/a4ba7ce45c693a404d6ed1351cdcdca1d80a3485) by Alice).
- Added conda virtual env instructions; note about output file format ([213da07](https://github.com/QUT-Digital-Observatory/youte/commit/213da07d0aa2398d66f5871df5a641d2faca8fd0) by Alice).
- add progresssaver to save search progress ([4ee1357](https://github.com/QUT-Digital-Observatory/youte/commit/4ee1357548be0d19555c4102cb38c931223098e4) by Boyd Nguyen).
- add hydrate command ([1a7d400](https://github.com/QUT-Digital-Observatory/youte/commit/1a7d400c3a1935903afbe4704ce2717e29fa9ca7) by Boyd Nguyen).
- add user config ([976fe2c](https://github.com/QUT-Digital-Observatory/youte/commit/976fe2ce29cc107d0a1a0d6b0ab5ef4296e43064) by Boyd Nguyen).
- add config ([3489c5a](https://github.com/QUT-Digital-Observatory/youte/commit/3489c5a4325a7f0cd2ac3a17fd4b6e5c71a1b60f) by Boyd Nguyen).
- add notes on stats and quota ([ca6a8f8](https://github.com/QUT-Digital-Observatory/youte/commit/ca6a8f87ad75e28a9a6275c39175a53d698025af) by Boyd Nguyen).
- add  param in the cli argument ([1ea4011](https://github.com/QUT-Digital-Observatory/youte/commit/1ea401169eebf9e09d307f1f0f246db0d419004c) by Boyd Nguyen).
- add setup config + CLI interface ([62dd16b](https://github.com/QUT-Digital-Observatory/youte/commit/62dd16b642cee4264915dcb35dd377f2e65a50ed) by Boyd Nguyen).
- add licence ([1b3aa7b](https://github.com/QUT-Digital-Observatory/youte/commit/1b3aa7b91322dd4d19e246d18323939649deeca9) by Boyd Nguyen).

### Fixed

- fix param and explain better ([3bd73ce](https://github.com/QUT-Digital-Observatory/youte/commit/3bd73ce4ad13af0090eea4e16316af4f2b5bcb4e) by Boyd Nguyen).
- fix error delete db in windows ([dff2035](https://github.com/QUT-Digital-Observatory/youte/commit/dff2035d94afc7c38d333b1dadfe2d8d5bc55584) by Boyd Nguyen).
- fix list-comments options ([30223fb](https://github.com/QUT-Digital-Observatory/youte/commit/30223fb2d5852344fa480f46cc972ac72d0c993a) by Boyd Nguyen).
- fix token residual carried to new parent/vid id ([a2123a6](https://github.com/QUT-Digital-Observatory/youte/commit/a2123a6a38b699ec381260deb364a3edec71b0d2) by Boyd Nguyen).
- fix eternal looping of list-comments ([5ea8917](https://github.com/QUT-Digital-Observatory/youte/commit/5ea89179e4bb459d85a8d84475919abc59486c65) by Boyd Nguyen).
- fix command help text ([1726e07](https://github.com/QUT-Digital-Observatory/youte/commit/1726e0735a6e9674904fb0ca05f34bc463a9f4b8) by Boyd Nguyen).
- Fix command typos ([e2305f2](https://github.com/QUT-Digital-Observatory/youte/commit/e2305f26285a95de146aaefb15e170138daf7666) by Boyd Nguyen).
- Fix command typo in the help ([c9a4291](https://github.com/QUT-Digital-Observatory/youte/commit/c9a42914c16d6c6e1173228b115d91d7e0c92050) by Sam Hames).
- fix anchor link ([e771eed](https://github.com/QUT-Digital-Observatory/youte/commit/e771eedf11250ffee6f427b0dd5b620f562c608c) by Boyd Nguyen).
- fix config location ([54fe8a0](https://github.com/QUT-Digital-Observatory/youte/commit/54fe8a0b5afe101b7818db1843f94f4dc7e83cc1) by Work).
- fix quota WIP ([62ce7a4](https://github.com/QUT-Digital-Observatory/youte/commit/62ce7a4afa1f68dc3377369b36048947969bad5d) by Boyd Nguyen).

### Changed

- changed version ([d47b4fc](https://github.com/QUT-Digital-Observatory/youte/commit/d47b4fca5c91030b5cff03aaef629916e92a80cc) by Boyd Nguyen).
- change local variable to avoid overlapping with outer scope var ([79dbb04](https://github.com/QUT-Digital-Observatory/youte/commit/79dbb042cffab46ff54342aa49bd91146120ed0f) by Boyd Nguyen).
- change installation instructions ([cfa20fb](https://github.com/QUT-Digital-Observatory/youte/commit/cfa20fb9b07389638b9dd1658c9c54e4681ddb2e) by Boyd Nguyen).
- change version + add long description ([441ecf7](https://github.com/QUT-Digital-Observatory/youte/commit/441ecf7288e95bf2580815e2139abf32fe87c8a1) by Boyd Nguyen).
- change output file ending to json or jsonl ([eba27c1](https://github.com/QUT-Digital-Observatory/youte/commit/eba27c1153f6a15d37647d8c73ae459631787b7f) by Boyd Nguyen).
- change tool name ([0cfcf49](https://github.com/QUT-Digital-Observatory/youte/commit/0cfcf4936fb3d95ad19c7c2e00411eb56266ede3) by Boyd Nguyen).
- change logging level ([0349f2d](https://github.com/QUT-Digital-Observatory/youte/commit/0349f2d8571db906f0abe8b2c9fd4908ab32705a) by Boyd Nguyen).

### Removed

- remove get-id option for now ([dbe715c](https://github.com/QUT-Digital-Observatory/youte/commit/dbe715c4486f3af524c2a43e2eb30389f3b6f862) by Boyd Nguyen).
- remove emojis ([35d499e](https://github.com/QUT-Digital-Observatory/youte/commit/35d499ea21441008a5a1060aae512d6c72ce6385) by Boyd Nguyen).
