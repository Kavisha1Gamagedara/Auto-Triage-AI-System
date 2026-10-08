import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';

/**
 * Telemetry3DAnimation
 * 4 High-tech, interactive 3D procedural animations representing the 4 Main Steps of Auto-Triage:
 * - 'intake' (Step 1): 3D Futuristic Car Wireframe with Sweeping Laser Grid Scanner & HUD Radar
 * - 'diagnosis' (Step 2): 3D Neural Diagnostic AI Core with Gyroscopic Rings & Pulsing Synapses
 * - 'procedures' (Step 3): 3D Holographic OEM Repair Manual Blueprint with Floating Exploded Layers
 * - 'procurement' (Step 4): 3D Multi-Tier Parts Vault with Floating Gold/Blue/Emerald Tier Pods & LKR Rings
 */
export default function Telemetry3DAnimation({ type = 'intake' }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 280;
    const height = container.clientHeight || 190;

    // 1. Scene & Camera Setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 0, 5.5);

    // 2. WebGL Renderer
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.35;
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.warn('WebGL initialization failed in Telemetry3DAnimation:', e);
      return;
    }

    // Responsive Canvas Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: newW, height: newH } = entry.contentRect;
        if (newW && newH && renderer) {
          camera.aspect = newW / newH;
          camera.updateProjectionMatrix();
          renderer.setSize(newW, newH);
        }
      }
    });
    resizeObserver.observe(container);

    // 3. Lighting Setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.8);
    dirLight1.position.set(5, 5, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x00f0ff, 1.4);
    dirLight2.position.set(-5, -2, -3);
    scene.add(dirLight2);

    const accentLight = new THREE.PointLight(0xff5e14, 2.5, 12);
    accentLight.position.set(0, 2, 4);
    scene.add(accentLight);

    // Root Group for interactive mouse damping
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    // Mouse Tracking for Interactive 3D Parallax Tilt
    let targetRotX = 0;
    let targetRotY = 0;

    const onMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetRotY = x * 0.45;
      targetRotX = -y * 0.35;
    };

    container.addEventListener('mousemove', onMouseMove);
    container.addEventListener('mouseleave', () => {
      targetRotX = 0;
      targetRotY = 0;
    });

    let animationFrameId;
    let time = 0;

    // =========================================================================
    // STEP 1: 3D HOLOGRAPHIC CAR CHASSIS & LASER SCANNER (INTAKE & VERIFY)
    // =========================================================================
    if (type === 'intake' || type === 'wheel') {
      const carGroup = new THREE.Group();
      mainGroup.add(carGroup);
      carGroup.position.y = -0.15;
      carGroup.rotation.y = 0.55;

      // 1. Aerodynamic Hypercar Body (Layered futuristic chassis)
      const bodyGeo = new THREE.BoxGeometry(2.8, 0.42, 1.3);
      const edgesGeo = new THREE.EdgesGeometry(bodyGeo);
      const wireMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, linewidth: 2 });
      const bodyWire = new THREE.LineSegments(edgesGeo, wireMat);
      carGroup.add(bodyWire);

      // Translucent Glass Body Core
      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0x051525,
        transparent: true,
        opacity: 0.65,
        roughness: 0.15,
        metalness: 0.85
      });
      const bodyMesh = new THREE.Mesh(bodyGeo, glassMat);
      carGroup.add(bodyMesh);

      // 2. Cockpit Canopy / Windshield Bubble
      const cabinGeo = new THREE.BoxGeometry(1.4, 0.45, 1.05);
      const cabinWire = new THREE.LineSegments(new THREE.EdgesGeometry(cabinGeo), new THREE.LineBasicMaterial({ color: 0xff5e14 }));
      cabinWire.position.set(-0.2, 0.4, 0);
      carGroup.add(cabinWire);

      const cabinMesh = new THREE.Mesh(cabinGeo, new THREE.MeshStandardMaterial({ color: 0x0d1624, roughness: 0.1, metalness: 0.9 }));
      cabinMesh.position.set(-0.2, 0.4, 0);
      carGroup.add(cabinMesh);

      // 3. Four Glowing Wireframe Wheels
      const wheelMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, roughness: 0.2, metalness: 0.9 });
      const wheelPositions = [
        [0.85, -0.15, 0.68],
        [-0.85, -0.15, 0.68],
        [0.85, -0.15, -0.68],
        [-0.85, -0.15, -0.68]
      ];
      const wheelMeshes = [];
      wheelPositions.forEach(([x, y, z]) => {
        const torus = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.1, 16, 24), wheelMat);
        torus.position.set(x, y, z);
        torus.rotation.y = Math.PI / 2;
        carGroup.add(torus);
        wheelMeshes.push(torus);
      });

      // 4. Ground Hexagonal Radar Scanner Ring
      const groundRingGeo = new THREE.RingGeometry(1.6, 1.7, 32);
      const groundRingMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.35, side: THREE.DoubleSide });
      const groundRing = new THREE.Mesh(groundRingGeo, groundRingMat);
      groundRing.rotation.x = Math.PI / 2;
      groundRing.position.y = -0.55;
      mainGroup.add(groundRing);

      // Inner Radar Crosshair Lines
      const crossLineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-1.6, -0.55, 0), new THREE.Vector3(1.6, -0.55, 0),
        new THREE.Vector3(0, -0.55, -1.6), new THREE.Vector3(0, -0.55, 1.6)
      ]);
      const crossLine = new THREE.LineSegments(crossLineGeo, new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.25 }));
      mainGroup.add(crossLine);

      // 5. Active Sweeping Laser Scanner Plane
      const scanPlaneGeo = new THREE.PlaneGeometry(0.08, 1.8);
      const scanPlaneMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide
      });
      const scanBeam = new THREE.Mesh(scanPlaneGeo, scanPlaneMat);
      scanBeam.rotation.y = Math.PI / 2;
      scanBeam.rotation.z = Math.PI / 2;
      carGroup.add(scanBeam);

      // Second Wide Laser Fan
      const scanFanGeo = new THREE.PlaneGeometry(0.4, 2.2);
      const scanFanMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.2,
        side: THREE.DoubleSide
      });
      const scanFan = new THREE.Mesh(scanFanGeo, scanFanMat);
      scanFan.rotation.y = Math.PI / 2;
      scanFan.rotation.z = Math.PI / 2;
      carGroup.add(scanFan);

      // Animation Loop
      const animate = () => {
        time += 0.025;

        // Floating zero-g car hover
        carGroup.position.y = -0.15 + Math.sin(time * 2.2) * 0.06;

        // Gentle 3/4 turn motion
        carGroup.rotation.y = 0.55 + Math.sin(time * 0.7) * 0.22;

        // Wheel spin
        wheelMeshes.forEach(w => {
          w.rotation.x += 0.04;
        });

        // Laser scan sweep from front to rear
        const scanX = Math.sin(time * 2.4) * 1.4;
        scanBeam.position.x = scanX;
        scanFan.position.x = scanX;

        // Ground radar rotation
        groundRing.rotation.z += 0.01;
        crossLine.rotation.y += 0.01;

        // Parallax damping
        mainGroup.rotation.y += (targetRotY - mainGroup.rotation.y) * 0.08;
        mainGroup.rotation.x += (targetRotX - mainGroup.rotation.x) * 0.08;

        renderer.render(scene, camera);
        animationFrameId = requestAnimationFrame(animate);
      };
      animate();
    }

    // =========================================================================
    // STEP 2: 3D NEURAL DIAGNOSTIC AI CORE (DIAGNOSTIC REASONING)
    // =========================================================================
    else if (type === 'diagnosis' || type === 'engine') {
      const brainGroup = new THREE.Group();
      mainGroup.add(brainGroup);

      // 1. Central Glowing Synaptic Core (Icosahedron)
      const coreGeo = new THREE.IcosahedronGeometry(0.85, 2);
      const coreMat = new THREE.MeshStandardMaterial({
        color: 0x111625,
        roughness: 0.2,
        metalness: 0.85,
        emissive: 0xff5e14,
        emissiveIntensity: 0.4
      });
      const coreMesh = new THREE.Mesh(coreGeo, coreMat);
      brainGroup.add(coreMesh);

      // Core Wireframe Facets
      const coreWire = new THREE.LineSegments(
        new THREE.EdgesGeometry(coreGeo),
        new THREE.LineBasicMaterial({ color: 0xffa048, transparent: true, opacity: 0.85 })
      );
      coreMesh.add(coreWire);

      // 2. Concentric Gyroscopic Orbit Rings
      const ring1Mat = new THREE.MeshStandardMaterial({ color: 0x3b82f6, metalness: 0.9, roughness: 0.2 });
      const ring2Mat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, metalness: 0.9, roughness: 0.2 });
      const ring3Mat = new THREE.MeshStandardMaterial({ color: 0xff5e14, metalness: 0.9, roughness: 0.2 });

      const ring1 = new THREE.Mesh(new THREE.TorusGeometry(1.22, 0.032, 16, 64), ring1Mat);
      const ring2 = new THREE.Mesh(new THREE.TorusGeometry(1.52, 0.032, 16, 64), ring2Mat);
      const ring3 = new THREE.Mesh(new THREE.TorusGeometry(1.82, 0.032, 16, 64), ring3Mat);

      brainGroup.add(ring1);
      brainGroup.add(ring2);
      brainGroup.add(ring3);

      // 3. Neural Synapse Floating Nodes (Orbiting data points)
      const nodeGeo = new THREE.SphereGeometry(0.08, 16, 16);
      const nodeMatCyan = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
      const nodeMatOrange = new THREE.MeshBasicMaterial({ color: 0xff5e14 });
      const nodeMatGreen = new THREE.MeshBasicMaterial({ color: 0x10b981 });

      const nodes = [];
      const nodeCount = 10;
      for (let i = 0; i < nodeCount; i++) {
        const phi = Math.acos(-1 + (2 * i) / nodeCount);
        const theta = Math.sqrt(nodeCount * Math.PI) * phi;
        const radius = 1.35 + (i % 3) * 0.25;

        const mat = i === 0 ? nodeMatOrange : i % 2 === 0 ? nodeMatCyan : nodeMatGreen;
        const node = new THREE.Mesh(nodeGeo, mat);
        node.position.set(
          radius * Math.cos(theta) * Math.sin(phi),
          radius * Math.sin(theta) * Math.sin(phi),
          radius * Math.cos(phi)
        );
        brainGroup.add(node);
        nodes.push({ mesh: node, basePos: node.position.clone(), speed: 0.5 + (i * 0.1) });
      }

      // 4. Floating Target Isolation Ring over Root-Cause Node
      const targetRing = new THREE.Mesh(
        new THREE.RingGeometry(0.18, 0.24, 24),
        new THREE.MeshBasicMaterial({ color: 0xff5e14, side: THREE.DoubleSide })
      );
      nodes[0].mesh.add(targetRing);

      // Animation Loop
      const animate = () => {
        time += 0.025;

        // Core pulsing & rotation
        coreMesh.rotation.y += 0.015;
        coreMesh.rotation.x += 0.008;
        const pulse = 1 + Math.sin(time * 3.5) * 0.08;
        coreMesh.scale.set(pulse, pulse, pulse);

        // Gyroscopic Ring Rotations
        ring1.rotation.x += 0.02;
        ring1.rotation.y += 0.015;

        ring2.rotation.y -= 0.025;
        ring2.rotation.z += 0.012;

        ring3.rotation.z += 0.018;
        ring3.rotation.x -= 0.015;

        // Neural Nodes floating orbit
        nodes.forEach((n, idx) => {
          n.mesh.position.x = n.basePos.x + Math.sin(time * n.speed + idx) * 0.12;
          n.mesh.position.y = n.basePos.y + Math.cos(time * n.speed + idx) * 0.12;
        });

        targetRing.rotation.z += 0.05;

        // Parallax damping
        mainGroup.rotation.y += (targetRotY - mainGroup.rotation.y) * 0.08;
        mainGroup.rotation.x += (targetRotX - mainGroup.rotation.x) * 0.08;

        renderer.render(scene, camera);
        animationFrameId = requestAnimationFrame(animate);
      };
      animate();
    }

    // =========================================================================
    // STEP 3: 3D OEM TECHNICAL REPAIR MANUAL & BLUEPRINT (PROCEDURES)
    // =========================================================================
    else if (type === 'procedures' || type === 'gears') {
      const blueprintGroup = new THREE.Group();
      mainGroup.add(blueprintGroup);
      blueprintGroup.rotation.x = 0.35;
      blueprintGroup.rotation.y = -0.3;

      // 1. Layered Floating Blueprint Glass Tablets (3 Disassembly Planes)
      const sheetGeo = new THREE.BoxGeometry(2.3, 1.6, 0.05);
      const sheetMat1 = new THREE.MeshPhysicalMaterial({
        color: 0x061e38,
        transparent: true,
        opacity: 0.65,
        roughness: 0.1,
        metalness: 0.8
      });
      const sheet1 = new THREE.Mesh(sheetGeo, sheetMat1);
      blueprintGroup.add(sheet1);

      // Blueprint Wireframe Borders
      const sheetWire1 = new THREE.LineSegments(new THREE.EdgesGeometry(sheetGeo), new THREE.LineBasicMaterial({ color: 0x00f0ff }));
      sheet1.add(sheetWire1);

      // Layer 2: Offset Diagnostic Procedure Layer
      const sheetMat2 = new THREE.MeshPhysicalMaterial({ color: 0x0c2540, transparent: true, opacity: 0.5, roughness: 0.1 });
      const sheet2 = new THREE.Mesh(new THREE.BoxGeometry(2.1, 1.4, 0.04), sheetMat2);
      sheet2.position.set(0.15, 0.15, 0.35);
      sheet2.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(2.1, 1.4, 0.04)), new THREE.LineBasicMaterial({ color: 0x10b981 })));
      blueprintGroup.add(sheet2);

      // 2. 3D Floating Wrench / Calibration Caliper (OEM Tool)
      const toolGroup = new THREE.Group();
      toolGroup.position.set(0, 0, 0.7);
      blueprintGroup.add(toolGroup);

      // Wrench Handle
      const handleMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.95, roughness: 0.15 });
      const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.6, 16), handleMat);
      handle.rotation.z = Math.PI / 4;
      toolGroup.add(handle);

      // Open Jaw Head
      const headMat = new THREE.MeshStandardMaterial({ color: 0xffa048, metalness: 0.9, roughness: 0.2 });
      const jaw = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.09, 16, 24, Math.PI * 1.5), headMat);
      jaw.position.set(0.58, 0.58, 0);
      jaw.rotation.z = Math.PI / 4;
      toolGroup.add(jaw);

      // 3. Torque Calibration Dial Ring (Factory Torques)
      const dialMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.85, side: THREE.DoubleSide });
      const torqueDial = new THREE.Mesh(new THREE.RingGeometry(0.45, 0.55, 32), dialMat);
      torqueDial.position.set(-0.55, -0.3, 0.45);
      blueprintGroup.add(torqueDial);

      // Torque Needle Indicator
      const needle = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.4, 0.02), new THREE.MeshBasicMaterial({ color: 0xff5e14 }));
      needle.position.set(-0.55, -0.15, 0.46);
      blueprintGroup.add(needle);

      // Animation Loop
      const animate = () => {
        time += 0.025;

        // Layer floating expansion & compression
        sheet2.position.z = 0.35 + Math.sin(time * 2) * 0.1;
        toolGroup.position.z = 0.7 + Math.sin(time * 2 + 1) * 0.12;
        toolGroup.rotation.z = Math.sin(time * 1.5) * 0.15;

        // Torque needle sweep
        needle.rotation.z = Math.sin(time * 3) * 1.2;

        // Tablet angle float
        blueprintGroup.rotation.y = -0.3 + Math.sin(time * 0.8) * 0.15;

        // Parallax damping
        mainGroup.rotation.y += (targetRotY - mainGroup.rotation.y) * 0.08;
        mainGroup.rotation.x += (targetRotX - mainGroup.rotation.x) * 0.08;

        renderer.render(scene, camera);
        animationFrameId = requestAnimationFrame(animate);
      };
      animate();
    }

    // =========================================================================
    // STEP 4: 3D MULTI-TIER PRICING & SOURCING VAULT (PROCUREMENT IN LKR)
    // =========================================================================
    else if (type === 'procurement' || type === 'gauge') {
      const vaultGroup = new THREE.Group();
      mainGroup.add(vaultGroup);
      vaultGroup.rotation.y = 0.4;

      // 1. Center Verification Cube / Safe (Procurement Core)
      const boxGeo = new THREE.BoxGeometry(1.1, 1.1, 1.1);
      const boxMat = new THREE.MeshStandardMaterial({
        color: 0x0f1522,
        roughness: 0.2,
        metalness: 0.85
      });
      const centerBox = new THREE.Mesh(boxGeo, boxMat);
      vaultGroup.add(centerBox);

      // Glowing Cyan Seams
      const boxWire = new THREE.LineSegments(new THREE.EdgesGeometry(boxGeo), new THREE.LineBasicMaterial({ color: 0x00f0ff, linewidth: 2 }));
      centerBox.add(boxWire);

      // 2. Three Floating Tier Pedestals (Gold OEM, Blue Certified, Emerald Economy)
      // Tier 1: Gold OEM Genuine
      const goldMat = new THREE.MeshStandardMaterial({ color: 0xffb800, metalness: 0.95, roughness: 0.15 });
      const goldPod = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.16, 24), goldMat);
      goldPod.position.set(0, 1.25, 0);
      vaultGroup.add(goldPod);

      // Tier 2: Blue Certified Aftermarket
      const blueMat = new THREE.MeshStandardMaterial({ color: 0x3b82f6, metalness: 0.9, roughness: 0.2 });
      const bluePod = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.14, 24), blueMat);
      bluePod.position.set(-1.25, -0.4, 0.4);
      vaultGroup.add(bluePod);

      // Tier 3: Emerald Economy
      const greenMat = new THREE.MeshStandardMaterial({ color: 0x10b981, metalness: 0.9, roughness: 0.2 });
      const greenPod = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.14, 24), greenMat);
      greenPod.position.set(1.25, -0.4, -0.4);
      vaultGroup.add(greenPod);

      // 3. Orbiting LKR Currency Rings / Orbital Ribbon
      const orbitRingMat = new THREE.MeshBasicMaterial({ color: 0xffa048, transparent: true, opacity: 0.4, side: THREE.DoubleSide });
      const orbitRing = new THREE.Mesh(new THREE.RingGeometry(1.65, 1.75, 48), orbitRingMat);
      orbitRing.rotation.x = Math.PI / 2.5;
      vaultGroup.add(orbitRing);

      // 4. Orbiting Price Tokens
      const tokenGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.05, 16);
      const tokenMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
      const tokens = [];
      for (let i = 0; i < 4; i++) {
        const token = new THREE.Mesh(tokenGeo, tokenMat);
        vaultGroup.add(token);
        tokens.push(token);
      }

      // Animation Loop
      const animate = () => {
        time += 0.025;

        // Center box gentle rotation & pulse
        centerBox.rotation.y += 0.012;
        centerBox.rotation.x = Math.sin(time * 1.2) * 0.1;

        // Tier Pods vertical floating hover
        goldPod.position.y = 1.25 + Math.sin(time * 2.5) * 0.12;
        goldPod.rotation.y += 0.03;

        bluePod.position.y = -0.4 + Math.sin(time * 2.5 + 1.2) * 0.1;
        bluePod.rotation.y += 0.025;

        greenPod.position.y = -0.4 + Math.sin(time * 2.5 + 2.4) * 0.1;
        greenPod.rotation.y += 0.025;

        // Currency orbit ring
        orbitRing.rotation.z += 0.015;

        // Tokens orbiting around perimeter
        tokens.forEach((tok, idx) => {
          const angle = time * 1.5 + (idx * Math.PI) / 2;
          tok.position.set(Math.cos(angle) * 1.7, Math.sin(angle * 0.8) * 0.5, Math.sin(angle) * 1.7);
          tok.rotation.x += 0.05;
        });

        // Parallax damping
        mainGroup.rotation.y += (targetRotY + 0.2 - mainGroup.rotation.y) * 0.08;
        mainGroup.rotation.x += (targetRotX - mainGroup.rotation.x) * 0.08;

        renderer.render(scene, camera);
        animationFrameId = requestAnimationFrame(animate);
      };
      animate();
    }

    // Cleanup on Unmount
    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener('mousemove', onMouseMove);
      if (resizeObserver) resizeObserver.disconnect();
      if (renderer && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
        renderer.dispose();
      }
      scene.clear();
    };
  }, [type]);

  return (
    <div 
      ref={mountRef} 
      className={`telemetry-3d-canvas-viewport type-${type}`}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        cursor: 'grab',
        touchAction: 'none'
      }}
    />
  );
}
