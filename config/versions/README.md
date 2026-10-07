# Pipeline configuration versions

`pipeline_cp23_provisional_20261004.yaml` records the D-068 development choice. It is passed explicitly to the CP2.3 end-to-end runner. K=20 and PARTIAL weight 0.5 remain provisional until the Part B result is reviewed.

The root `config/pipeline_v1.yaml` is the historical runtime verification baseline. Frozen experiment plans hash its path and bytes. Do not replace or rename it to make the provisional settings appear active. CP3 promotion needs a new version identifier, updated runtime loader, regression tests, and a clear decision record. The backup in `config/archive/` preserves the same historical bytes.

`pipeline_cp23_provisional_v2_20261004.yaml` records D-077: DeepSeek Flash for offline JD extraction, GPT-6 Luna for online evidence matching, H2v2 holds (D-072), the stage-1 seniority rule (D-074) and product order (D-073). K and PARTIAL weight stay provisional until the D-078 rule is applied. It is not yet loaded by the runtime.

`pipeline_cp23_provisional_v3_20261004.yaml` records D-083: GPT-6 Sol for evidence matching, GPT-6 Luna as the low-cost fallback, DeepSeek Flash for extraction. Other settings as in v2. K and PARTIAL weight stay provisional until the D-078 rule runs. Not yet loaded by the runtime.
