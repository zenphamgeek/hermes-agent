import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";

import {
  cameraOf,
  slabOf,
  cylinder,
  solidSvg,
  figureSvg,
} from "../.agents/skills/anatomy/kit/iso-kit.mjs";
import {
  frameAlong,
  prismOf,
} from "../.agents/skills/anatomy/kit/lathe.mjs";
import {
  tubePieces,
  tubeSvg,
} from "../.agents/skills/anatomy/kit/tube.mjs";
import * as A from "../.agents/skills/anatomy/kit/audit.mjs";

/**
 * Extract flat list of failure records from an `A.audit(R, P)` result object
 * while preserving compatibility with `A.failures(result)` numeric count.
 */
function failures(result) {
  if (!result || typeof result !== "object") return [];
  return [
    ...(result.clearance ?? []),
    ...(result.apart ?? []),
    ...(result.flight ?? []),
    ...(result.crowding ?? []),
    ...(result.cover ?? []),
    ...(result.terminals ?? []),
    ...(result.loose ?? []).filter((e) => !e.free),
    ...(result.folds ?? []),
    ...(result.supports?.loose ?? []),
    ...(result.supports?.hanging ?? []),
    ...(result.supports?.sunk ?? []),
    ...(result.depth?.problems ?? []),
    ...(result.depth?.missing ?? []),
    ...(result.self ?? []),
    ...(result.wobble ?? []),
    ...(result.seats ?? []),
  ];
}

class SovereignStateTransitionError extends Error {
  constructor(fromState, event, message) {
    super(message || `Illegal state transition from '${fromState}' via '${event}'`);
    this.name = "SovereignStateTransitionError";
    this.fromState = fromState;
    this.event = event;
  }
}

class SovereignBoundaryError extends Error {
  constructor(code, detail) {
    super(`Boundary violation [${code}]: ${detail}`);
    this.name = "SovereignBoundaryError";
    this.code = code;
  }
}

class SovereignOptimisticLockError extends Error {
  constructor(entityId, expectedVersion, actualVersion) {
    super(`CAS version mismatch on ${entityId}: expected v${expectedVersion}, actual v${actualVersion}`);
    this.name = "SovereignOptimisticLockError";
    this.entityId = entityId;
    this.expectedVersion = expectedVersion;
    this.actualVersion = actualVersion;
  }
}

/**
 * Build a deterministic Sovereign Anatomy Isometric Rig (`ProFirstManifoldRig`)
 * using real `cameraOf`, `slabOf`, `cylinder`, `tubePieces`, `A.recorder`, `A.settle`, and `A.audit`.
 */
function buildProFirstManifoldRig(projectionOverrides = {}) {
  const P = {
    origin: [320, 220],
    scale: 3.2,
    azimuth: 45,
    elevation: 30,
    ...projectionOverrides,
  };
  const cam = cameraOf(P);
  const R = A.recorder(P);

  // 1. Grounded Stand Base Slab (z: 0 -> 6)
  const basePlan = { x: -34, y: -16, w: 68, d: 32, r: 3 };
  const baseSolid = R.solid(A.slab(basePlan, 0, 6, { name: "stand.base", ground: true }));
  const baseSvg = solidSvg(slabOf(basePlan, 0, 6, P), { tone: "lo", halo: true });
  R.put({
    name: "stand.base",
    piece: "stand",
    at: [0, 0, 3],
    shapes: [baseSolid],
    svg: baseSvg,
  });

  // 2. Left Pro Manifold Block (x: -26..-14, y: -8..8, z: 6..22) sitting flush on stand.base
  const leftPlan = { x: -26, y: -8, w: 12, d: 16, r: 1 };
  const leftSolid = R.solid(A.slab(leftPlan, 6, 16, { name: "manifold.left" }));
  const leftSvg = solidSvg(slabOf(leftPlan, 6, 16, P), { tone: "mid" });
  R.put({
    name: "manifold.left",
    piece: "manifold",
    at: [-20, 0, 14],
    shapes: [leftSolid],
    svg: leftSvg,
  });

  // 3. Right Ultra Manifold Block (x: 14..26, y: -8..8, z: 6..22) sitting flush on stand.base
  const rightPlan = { x: 14, y: -8, w: 12, d: 16, r: 1 };
  const rightSolid = R.solid(A.slab(rightPlan, 6, 16, { name: "manifold.right" }));
  const rightSvg = solidSvg(slabOf(rightPlan, 6, 16, P), { tone: "mid" });
  R.put({
    name: "manifold.right",
    piece: "manifold",
    at: [20, 0, 14],
    shapes: [rightSolid],
    svg: rightSvg,
  });

  // 4. Left & Right Cylindrical Regulator Turrets sitting flush at z: 22..28
  const leftTurret = R.solid(A.cylinder(-20, 0, 4, 22, 6, { name: "turret.left" }));
  const leftTurretSvg = solidSvg(cylinder(-20, 0, 4, 22, 6, P), { tone: "hi", lit: true });
  R.put({
    name: "turret.left",
    piece: "turret",
    at: [-20, 0, 25],
    shapes: [leftTurret],
    svg: leftTurretSvg,
  });

  const rightTurret = R.solid(A.cylinder(20, 0, 4, 22, 6, { name: "turret.right" }));
  const rightTurretSvg = solidSvg(cylinder(20, 0, 4, 22, 6, P), { tone: "hi" });
  R.put({
    name: "turret.right",
    piece: "turret",
    at: [20, 0, 25],
    shapes: [rightTurret],
    svg: rightTurretSvg,
  });

  // 5. Horizontal Conduit Pipe connecting manifold.left (x = -14) to manifold.right (x = 14) at z = 14
  const routePoints = [
    [-14, 0, 14],
    [14, 0, 14],
  ];
  const tubeRadius = 1.2;
  const recordedTubes = R.route("conduit.bridge", routePoints, tubeRadius, {
    piece: "conduit",
    ends: [true, true],
  });
  const pieces = tubePieces(routePoints, tubeRadius, P, { maxLength: 40 });
  const conduitSvg = pieces.map((piece) => tubeSvg(piece, { tone: "hi" })).join("");
  R.put({
    name: "conduit.bridge",
    route: "conduit.bridge",
    piece: "conduit",
    at: [0, 0, 14],
    shapes: recordedTubes,
    svg: conduitSvg,
  });

  const settled = A.settle(R, P);
  const auditResult = A.audit(R, P);
  const orderedSvg = settled.items
    .slice()
    .sort((a, b) => a.key - b.key)
    .map((item) => item.svg)
    .join("");
  const svgDocument = figureSvg({
    width: 640,
    height: 440,
    label: "ProFirstManifoldRig",
    body: orderedSvg,
  });

  return { P, cam, R, settled, auditResult, svgDocument };
}

/**
 * Formal State Machine S x E -> S' for Sovereign Anatomy Isometric Rig
 * States: Draft, Confirmed, Audited, Published, Cancelled
 */
const TRANSITION_TABLE = Object.freeze({
  Draft: Object.freeze({
    CONFIRM: "Confirmed",
    CANCEL: "Cancelled",
  }),
  Confirmed: Object.freeze({
    AUDIT: "Audited",
    CANCEL: "Cancelled",
  }),
  Audited: Object.freeze({
    PUBLISH: "Published",
    CANCEL: "Cancelled",
  }),
  Published: Object.freeze({}),
  Cancelled: Object.freeze({}),
});

class ProFirstManifoldRigStateMachine {
  constructor(rigId = "rig-pro-first-001") {
    this.rigId = rigId;
    this.state = "Draft";
    this.history = ["Draft"];
    this.rigBundle = null;
    this.auditSummary = null;
    this.stateDigest = this._computeDigest();
  }

  _computeDigest() {
    const canonical = JSON.stringify({
      rigId: this.rigId,
      state: this.state,
      history: this.history,
      failureCount: this.auditSummary ? this.auditSummary.failureCount : null,
      svgSha256: this.rigBundle
        ? crypto.createHash("sha256").update(this.rigBundle.svgDocument).digest("hex")
        : null,
    });
    return crypto.createHash("sha256").update(canonical).digest("hex");
  }

  transition(event) {
    const allowed = TRANSITION_TABLE[this.state];
    if (!allowed || !Object.prototype.hasOwnProperty.call(allowed, event)) {
      throw new SovereignStateTransitionError(
        this.state,
        event,
        `Forbidden transition: ${this.state} --(${event})--> ?`
      );
    }

    const nextState = allowed[event];
    if (event === "CONFIRM") {
      this.rigBundle = buildProFirstManifoldRig();
    } else if (event === "AUDIT") {
      if (!this.rigBundle) {
        throw new SovereignStateTransitionError(this.state, event, "Rig geometry missing before AUDIT");
      }
      const failList = failures(this.rigBundle.auditResult);
      const failCount = A.failures(this.rigBundle.auditResult);
      if (failList.length > 0 || failCount > 0) {
        throw new SovereignStateTransitionError(
          this.state,
          event,
          `Audit gate failed with ${failCount} collisions`
        );
      }
      this.auditSummary = {
        failureCount: failCount,
        failuresLength: failList.length,
        solidsCount: this.rigBundle.R.solids.length,
        tubesCount: this.rigBundle.R.tubes.length,
        itemsCount: this.rigBundle.R.items.length,
      };
    }

    this.state = nextState;
    this.history.push(nextState);
    this.stateDigest = this._computeDigest();
    return {
      state: this.state,
      stateDigest: this.stateDigest,
      history: [...this.history],
    };
  }
}

/**
 * Boundary validation & safe prism wrapper for Vector 3 poison-pill testing.
 */
function hasSelfIntersection(polygon) {
  const n = polygon.length;
  if (n < 3) return true;
  const ccw = (A, B, C) => (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0]);
  const segmentsIntersect = (p1, p2, p3, p4) =>
    ccw(p1, p3, p4) !== ccw(p2, p3, p4) && ccw(p1, p2, p3) !== ccw(p1, p2, p4);

  for (let i = 0; i < n; i++) {
    const a1 = polygon[i];
    const a2 = polygon[(i + 1) % n];
    if (Math.hypot(a2[0] - a1[0], a2[1] - a1[1]) < 1e-9) return true;
    for (let j = i + 2; j < n; j++) {
      if (i === 0 && j === n - 1) continue;
      const b1 = polygon[j];
      const b2 = polygon[(j + 1) % n];
      if (segmentsIntersect(a1, a2, b1, b2)) return true;
    }
  }
  return false;
}

function isConcavePolygon(polygon) {
  const n = polygon.length;
  if (n < 3) return false;
  let sign = 0;
  for (let i = 0; i < n; i++) {
    const [x0, y0] = polygon[i];
    const [x1, y1] = polygon[(i + 1) % n];
    const [x2, y2] = polygon[(i + 2) % n];
    const cross = (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1);
    if (Math.abs(cross) > 1e-9) {
      const currentSign = Math.sign(cross);
      if (sign === 0) sign = currentSign;
      else if (sign !== currentSign) return true;
    }
  }
  return false;
}

function detectCyclicObject(value, seen = new WeakSet()) {
  if (value === null || typeof value !== "object") return false;
  if (seen.has(value)) return true;
  seen.add(value);
  if (Array.isArray(value)) {
    for (const item of value) {
      if (detectCyclicObject(item, seen)) return true;
    }
  } else {
    for (const key of Object.keys(value)) {
      if (detectCyclicObject(value[key], seen)) return true;
    }
  }
  seen.delete(value);
  return false;
}

const MAX_GEOMETRY_COORD = 1e6;

function safeSovereignPrism(F, polygon, s0, s1, P, metadata = {}) {
  if (detectCyclicObject(metadata) || detectCyclicObject(polygon) || detectCyclicObject(P)) {
    throw new SovereignBoundaryError("CYCLIC_PAYLOAD", "Cyclic reference detected in rig payload");
  }
  if (!metadata || metadata.key === null || metadata.key === "") {
    throw new SovereignBoundaryError("NULL_KEY", "Entity key must be a non-empty string");
  }
  for (const [label, num] of [
    ["s0", s0],
    ["s1", s1],
    ["P.scale", P?.scale],
  ]) {
    if (typeof num !== "number" || !Number.isFinite(num)) {
      throw new SovereignBoundaryError("NON_FINITE_NUMBER", `${label} must be finite, got ${num}`);
    }
    if (Math.abs(num) > MAX_GEOMETRY_COORD) {
      throw new SovereignBoundaryError("OVERFLOW_BOUND", `${label} exceeds MAX_GEOMETRY_COORD (${num})`);
    }
  }
  if (P.scale <= 0 || s1 - s0 <= 0) {
    throw new SovereignBoundaryError("NEGATIVE_OR_ZERO_DIMENSION", `Invalid scale=${P.scale} or span=${s1 - s0}`);
  }
  if (!Array.isArray(polygon) || polygon.length < 3) {
    throw new SovereignBoundaryError("DEGENERATE_POLYGON", "Polygon requires at least 3 vertices");
  }
  for (const pt of polygon) {
    if (
      !Array.isArray(pt) ||
      pt.length < 2 ||
      !Number.isFinite(pt[0]) ||
      !Number.isFinite(pt[1]) ||
      Math.abs(pt[0]) > MAX_GEOMETRY_COORD ||
      Math.abs(pt[1]) > MAX_GEOMETRY_COORD
    ) {
      throw new SovereignBoundaryError("INVALID_VERTEX", `Invalid polygon vertex: ${JSON.stringify(pt)}`);
    }
  }
  if (hasSelfIntersection(polygon)) {
    throw new SovereignBoundaryError("SELF_INTERSECTING_POLYGON", "Polygon edges self-intersect");
  }
  if (isConcavePolygon(polygon) && !metadata.allowConcave) {
    throw new SovereignBoundaryError("CONCAVE_POLYGON_REJECTED", "Concave polygon rejected by strict convex hull policy");
  }
  return prismOf(F, polygon, s0, s1, P);
}

// ============================================================================
// Vector 1: State Machine Invariant Proof
// ============================================================================
test("Vector 1 (State Machine Invariant Proof): S x E -> S' with 0 audit collisions and deterministic SHA-256 digest", () => {
  const sm1 = new ProFirstManifoldRigStateMachine("rig-sovereign-v1");
  const sm2 = new ProFirstManifoldRigStateMachine("rig-sovereign-v1");

  assert.strictEqual(sm1.state, "Draft");
  assert.strictEqual(sm1.stateDigest, sm2.stateDigest);

  // Illegal jump directly from Draft -> Published must throw SovereignStateTransitionError
  assert.throws(
    () => sm1.transition("PUBLISH"),
    (err) => err instanceof SovereignStateTransitionError && err.fromState === "Draft" && err.event === "PUBLISH"
  );

  // Valid progression: Draft -> Confirmed -> Audited -> Published
  const stepConfirm1 = sm1.transition("CONFIRM");
  const stepConfirm2 = sm2.transition("CONFIRM");
  assert.strictEqual(stepConfirm1.state, "Confirmed");
  assert.strictEqual(stepConfirm1.stateDigest, stepConfirm2.stateDigest);

  // Verify real anatomy geometry & audit zero-collision invariant
  const { auditResult, R, settled, cam } = sm1.rigBundle;
  assert.ok(cam.k > 0 && Number.isFinite(cam.sinA) && Number.isFinite(cam.cosE));
  assert.strictEqual(R.solids.length, 5);
  assert.strictEqual(R.tubes.length, 1);
  assert.strictEqual(settled.items.length, 6);
  assert.strictEqual(failures(auditResult).length, 0, `Expected 0 failures, got: ${A.report(auditResult)}`);
  assert.strictEqual(A.failures(auditResult), 0);

  const stepAudit1 = sm1.transition("AUDIT");
  const stepAudit2 = sm2.transition("AUDIT");
  assert.strictEqual(stepAudit1.state, "Audited");
  assert.strictEqual(stepAudit1.stateDigest, stepAudit2.stateDigest);

  const stepPublish1 = sm1.transition("PUBLISH");
  const stepPublish2 = sm2.transition("PUBLISH");
  assert.strictEqual(stepPublish1.state, "Published");
  assert.strictEqual(stepPublish1.stateDigest, stepPublish2.stateDigest);
  assert.deepStrictEqual(stepPublish1.history, ["Draft", "Confirmed", "Audited", "Published"]);

  // Terminal Cancelled path: Draft -> Cancelled, then Cancelled -> Published must throw
  const smCancelled = new ProFirstManifoldRigStateMachine("rig-sovereign-cancelled");
  smCancelled.transition("CANCEL");
  assert.strictEqual(smCancelled.state, "Cancelled");
  assert.throws(
    () => smCancelled.transition("PUBLISH"),
    (err) => err instanceof SovereignStateTransitionError && err.fromState === "Cancelled" && err.event === "PUBLISH"
  );
});

// ============================================================================
// Vector 2: Concurrency Race Interleaving (16 Parallel Async Mutations + CAS)
// ============================================================================
test("Vector 2 (Concurrency Race Interleaving): 16 parallel async mutations with optimistic CAS locking", async () => {
  class OptimisticRigStore {
    constructor(entityId) {
      this.entityId = entityId;
      this.record = {
        entityId,
        version: 0,
        logicalTimestamp: 1000,
        appliedMutations: [],
        scale: 3.2,
      };
    }

    async readSnapshot() {
      await new Promise((resolve) => setImmediate(resolve));
      return structuredClone(this.record);
    }

    async compareAndSwap(expectedVersion,expectedTimestamp, mutatorFn) {
      await new Promise((resolve) => setImmediate(resolve));
      if (
        this.record.version !== expectedVersion ||
        this.record.logicalTimestamp !== expectedTimestamp
      ) {
        throw new SovereignOptimisticLockError(this.entityId, expectedVersion, this.record.version);
      }
      const next = mutatorFn(structuredClone(this.record));
      this.record = {
        ...next,
        version: this.record.version + 1,
        logicalTimestamp: this.record.logicalTimestamp + 1,
      };
      return structuredClone(this.record);
    }
  }

  const store = new OptimisticRigStore("rig-cas-entity-001");
  const WORKER_COUNT = 16;
  let casConflictsObserved = 0;

  async function runWorkerWithRetry(workerId) {
    for (let attempt = 0; attempt < 64; attempt++) {
      const snap = await store.readSnapshot();
      try {
        const committed = await store.compareAndSwap(
          snap.version,
          snap.logicalTimestamp,
          (draft) => {
            draft.appliedMutations.push({
              workerId,
              baseVersion: snap.version,
              nextVersion: snap.version + 1,
            });
            draft.scale = Number((draft.scale + 0.05).toFixed(4));
            return draft;
          }
        );
        return committed.version;
      } catch (err) {
        if (err instanceof SovereignOptimisticLockError) {
          casConflictsObserved++;
          // Deterministic micro-yield before retry
          await new Promise((resolve) => setTimeout(resolve, (workerId + attempt) % 3));
          continue;
        }
        throw err;
      }
    }
    throw new Error(`Worker ${workerId} exhausted CAS retries`);
  }

  const results = await Promise.all(
    Array.from({ length: WORKER_COUNT }, (_, idx) => runWorkerWithRetry(idx))
  );

  // Verify zero lost updates and strict monotonic version progression 1..16
  assert.strictEqual(store.record.version, WORKER_COUNT);
  assert.strictEqual(store.record.logicalTimestamp, 1000 + WORKER_COUNT);
  assert.strictEqual(store.record.appliedMutations.length, WORKER_COUNT);
  assert.ok(casConflictsObserved > 0, "Expected real CAS contention across 16 concurrent workers");

  const committedVersions = store.record.appliedMutations.map((m) => m.nextVersion);
  assert.deepStrictEqual(
    committedVersions,
    Array.from({ length: WORKER_COUNT }, (_, i) => i + 1)
  );

  const uniqueWorkers = new Set(store.record.appliedMutations.map((m) => m.workerId));
  assert.strictEqual(uniqueWorkers.size, WORKER_COUNT);
  assert.strictEqual([...results].sort((a, b) => a - b).length, WORKER_COUNT);
});

// ============================================================================
// Vector 3: Boundary Value Stress & Poison Pills
// ============================================================================
test("Vector 3 (Boundary Value Stress & Poison Pills): NaN, Infinity, -1, MAX_SAFE_INTEGER, concave/self-intersecting polygons, null keys, cyclic payloads", () => {
  const P = { origin: [320, 220], scale: 3.2, azimuth: 45, elevation: 30 };
  const F = frameAlong([0, 0, 6], [0, 0, 1]);
  const validSquare = [
    [-6, -6],
    [6, -6],
    [6, 6],
    [-6, 6],
  ];

  // Baseline valid convex prism succeeds
  const validOut = safeSovereignPrism(F, validSquare, 0, 10, P, { key: "prism.valid" });
  assert.ok(validOut.fill.startsWith("M") && validOut.outline.endsWith("Z"));

  // 1. NaN injection
  assert.throws(
    () => safeSovereignPrism(F, validSquare, NaN, 10, P, { key: "prism.nan" }),
    (err) => err instanceof SovereignBoundaryError && err.code === "NON_FINITE_NUMBER"
  );

  // 2. Infinity injection
  assert.throws(
    () => safeSovereignPrism(F, validSquare, 0, Infinity, P, { key: "prism.inf" }),
    (err) => err instanceof SovereignBoundaryError && err.code === "NON_FINITE_NUMBER"
  );

  // 3. -1 negative scale / inverted span injection
  assert.throws(
    () => safeSovereignPrism(F, validSquare, 10, 9, { ...P, scale: -1 }, { key: "prism.neg" }),
    (err) => err instanceof SovereignBoundaryError && err.code === "NEGATIVE_OR_ZERO_DIMENSION"
  );

  // 4. Number.MAX_SAFE_INTEGER overflow injection
  assert.throws(
    () =>
      safeSovereignPrism(F, validSquare, 0, Number.MAX_SAFE_INTEGER, P, {
        key: "prism.max_safe_int",
      }),
    (err) => err instanceof SovereignBoundaryError && err.code === "OVERFLOW_BOUND"
  );

  // 5. Self-intersecting bowtie polygon into prismOf & boundary guard
  const bowtiePolygon = [
    [-8, -8],
    [8, 8],
    [8, -8],
    [-8, 8],
  ];
  const rawBowtiePrism = prismOf(F, bowtiePolygon, 0, 8, P);
  assert.strictEqual(typeof rawBowtiePrism.fill, "string");
  assert.throws(
    () => safeSovereignPrism(F, bowtiePolygon, 0, 8, P, { key: "prism.bowtie" }),
    (err) => err instanceof SovereignBoundaryError && err.code === "SELF_INTERSECTING_POLYGON"
  );

  // 6. Concave L-shaped polygon into prismOf & strict convex policy rejection
  const concaveLPolygon = [
    [-8, -8],
    [8, -8],
    [8, 0],
    [0, 0],
    [0, 8],
    [-8, 8],
  ];
  const rawConcavePrism = prismOf(F, concaveLPolygon, 0, 8, P);
  assert.ok(rawConcavePrism.fill.length > 0 && rawConcavePrism.outline.length > 0);
  assert.throws(
    () => safeSovereignPrism(F, concaveLPolygon, 0, 8, P, { key: "prism.concave" }),
    (err) => err instanceof SovereignBoundaryError && err.code === "CONCAVE_POLYGON_REJECTED"
  );

  // 7. Null key injection
  assert.throws(
    () => safeSovereignPrism(F, validSquare, 0, 10, P, { key: null }),
    (err) => err instanceof SovereignBoundaryError && err.code === "NULL_KEY"
  );

  // 8. Cyclic payload injection
  const cyclicMeta = { key: "prism.cyclic" };
  cyclicMeta.self = cyclicMeta;
  assert.throws(
    () => safeSovereignPrism(F, validSquare, 0, 10, P, cyclicMeta),
    (err) => err instanceof SovereignBoundaryError && err.code === "CYCLIC_PAYLOAD"
  );
});

// ============================================================================
// Vector 4: Partial Failure & Clean Rollback (3-Step Atomic Rig Transaction)
// ============================================================================
test("Vector 4 (Partial Failure & Clean Rollback): Fault at step 2 rolls back 100% to pre-transaction snapshot with cache invalidation", () => {
  class AtomicRigTransactionManager {
    constructor() {
      this.ledger = new Map();
      this.geometryStore = new Map();
      this.projectionCache = new Map();
      this.commitSeq = 0;
    }

    seedInitialState(rigId, rigData) {
      this.geometryStore.set(rigId, structuredClone(rigData));
      this.ledger.set(rigId, {
        rigId,
        commitSeq: ++this.commitSeq,
        svgSha256: crypto.createHash("sha256").update(rigData.svgDocument).digest("hex"),
      });
      this.projectionCache.set(rigId, { cachedAt: 1000, svgDocument: rigData.svgDocument });
    }

    snapshot() {
      return {
        commitSeq: this.commitSeq,
        ledgerEntries: structuredClone([...this.ledger.entries()]),
        geometryEntries: structuredClone([...this.geometryStore.entries()]),
      };
    }

    executeThreeStepTransaction(rigId, { injectStep2Fault = false } = {}) {
      const preSnap = this.snapshot();
      const stagedOrphans = [];

      try {
        // Step 1: Geometry Build & Staging + Cache Pre-population
        const built = buildProFirstManifoldRig({ scale: 3.6 });
        const stagingKey = `${rigId}::staging`;
        stagedOrphans.push(stagingKey);
        this.geometryStore.set(stagingKey, { svgDocument: built.svgDocument });
        this.geometryStore.set(rigId, { svgDocument: built.svgDocument });
        this.projectionCache.set(rigId, { cachedAt: 2000, svgDocument: built.svgDocument });

        // Step 2: Audit Gate Verification (Injected Fault)
        if (injectStep2Fault) {
          // Simulate an intersecting solid collision discovered at the audit gate
          const collidingR = built.R;
          const clashingSolid = collidingR.solid(
            A.cylinder(0, 0, 5, 10, 8, { name: "fault.collider" })
          );
          collidingR.put({
            name: "fault.collider",
            piece: "conduit",
            shapes: [clashingSolid],
            svg: solidSvg(cylinder(0, 0, 5, 10, 8, built.P)),
          });
          const faultAudit = A.audit(collidingR, built.P);
          if (A.failures(faultAudit) > 0 || failures(faultAudit).length > 0) {
            throw new Error(`Step 2 Audit Gate Fault: ${A.failures(faultAudit)} geometric violations`);
          }
        }

        // Step 3: Ledger Commit
        this.geometryStore.delete(stagingKey);
        this.ledger.set(rigId, {
          rigId,
          commitSeq: ++this.commitSeq,
          svgSha256: crypto.createHash("sha256").update(built.svgDocument).digest("hex"),
        });
        return { committed: true };
      } catch (err) {
        // Atomic Rollback to Pre-Transaction Snapshot & Cache Invalidation
        this.commitSeq = preSnap.commitSeq;
        this.ledger = new Map(structuredClone(preSnap.ledgerEntries));
        this.geometryStore = new Map(structuredClone(preSnap.geometryEntries));
        for (const orphanKey of stagedOrphans) {
          this.geometryStore.delete(orphanKey);
        }
        this.projectionCache.delete(rigId);
        throw err;
      }
    }
  }

  const txManager = new AtomicRigTransactionManager();
  const initialRig = buildProFirstManifoldRig({ scale: 3.2 });
  txManager.seedInitialState("rig-atomic-001", { svgDocument: initialRig.svgDocument });

  const beforeSnap = txManager.snapshot();
  assert.strictEqual(txManager.projectionCache.has("rig-atomic-001"), true);

  // Execute transaction with injected Step 2 Audit Gate fault
  assert.throws(
    () => txManager.executeThreeStepTransaction("rig-atomic-001", { injectStep2Fault: true }),
    /Step 2 Audit Gate Fault/
  );

  // Verify 100% rollback to pre-transaction snapshot, zero orphaned staging records, and cache invalidation
  const afterSnap = txManager.snapshot();
  assert.deepStrictEqual(afterSnap, beforeSnap);
  assert.strictEqual(txManager.geometryStore.has("rig-atomic-001::staging"), false);
  assert.strictEqual(txManager.projectionCache.has("rig-atomic-001"), false);
});
