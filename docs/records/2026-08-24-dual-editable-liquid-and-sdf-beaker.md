# Dual-entry liquid and standard SDF beaker

ConvertAsset added request/result v3 for dual frozen/editable liquid delivery.
Every liquid has an independent ParticleSet and particleGroup, while all sets
share one ParticleSystem and one transparent-blue material. The editable entry
retains a height-only PhysX cylinder sampler; the frozen entry receives the
settled points from the successful Isaac 4.1 validation run.

The Wangshuai 325 mL beaker was packaged behind a metre/Z-up `/World` facade.
The source USD is unchanged. Its body and rim retain the complete
PhysxSDFMeshCollisionAPI configuration, its spout uses convexHull, and its
glass inputs exactly match WebStandardClearBorosilicate. The raw source's
centimetre stage metadata and absolute OmniGlass dependency are not exposed to
consumers.

The magnetic-stir-bar consumer run used 969 particles. Isaac Sim 4.1 observed
100% retention, zero below-floor particles, one active PhysicsScene, and no
target hard errors. Fill-ratio matching is diagnostic for v3 because changing
the sampler height intentionally invalidates the original ratio.
