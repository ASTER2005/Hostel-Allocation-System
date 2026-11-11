/**
 * Hostel Allocation and Management System
 * Architectural 3D Exploration Module (Three.js + OrbitControls)
 * Provides realistic 3D building exterior, floor cutaway, and room interior views.
 */

class Hostel3DViewer {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.options = Object.assign({
      mode: 'building', // 'building', 'floor', 'room'
      roomType: 'Double', // 'Single', 'Double', 'Triple'
      enableAutoRotate: false,
      onRoomSelect: null
    }, options);

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.currentMeshGroup = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.clickableObjects = [];

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 600;
    const height = this.container.clientHeight || 420;

    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xF4F1E9);
    this.scene.fog = new THREE.FogExp2(0xF4F1E9, 0.015);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(24, 18, 28);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxPolarAngle = Math.PI / 2 - 0.05; // Prevent dipping beneath ground
      this.controls.minDistance = 6;
      this.controls.maxDistance = 75;
      this.controls.autoRotate = this.options.enableAutoRotate;
      this.controls.autoRotateSpeed = 1.0;
    }

    // 5. Lighting: Warm natural architectural lighting
    this.setupLighting();

    // 6. Build initial geometry
    this.buildMode(this.options.mode);

    // 7. Event Listeners
    window.addEventListener('resize', () => this.onWindowResize());
    this.renderer.domElement.addEventListener('pointerdown', (e) => this.onPointerDown(e));

    // 8. Render loop
    this.animate();
  }

  setupLighting() {
    // Ambient light with warm ivory hue
    const ambientLight = new THREE.AmbientLight(0xfff8ee, 0.75);
    this.scene.add(ambientLight);

    // Directional Sun Light
    const sunLight = new THREE.DirectionalLight(0xfff3db, 1.2);
    sunLight.position.set(30, 45, 25);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 120;
    sunLight.shadow.camera.left = -25;
    sunLight.shadow.camera.right = 25;
    sunLight.shadow.camera.top = 25;
    sunLight.shadow.camera.bottom = -25;
    sunLight.shadow.bias = -0.0005;
    this.scene.add(sunLight);

    // Subtle sky-ground hemisphere fill
    const hemiLight = new THREE.HemisphereLight(0xe8edf2, 0xdcd6c8, 0.4);
    this.scene.add(hemiLight);
  }

  clearScene() {
    if (this.currentMeshGroup) {
      this.scene.remove(this.currentMeshGroup);
      this.currentMeshGroup = null;
    }
    this.clickableObjects = [];
  }

  buildMode(mode, subParam = null) {
    this.clearScene();
    this.options.mode = mode;
    this.currentMeshGroup = new THREE.Group();

    if (mode === 'building') {
      this.buildBuildingModel();
      this.camera.position.set(26, 18, 30);
      if (this.controls) this.controls.target.set(0, 5, 0);
    } else if (mode === 'floor') {
      this.buildFloorCutawayModel();
      this.camera.position.set(18, 22, 22);
      if (this.controls) this.controls.target.set(0, 1, 0);
    } else if (mode === 'room') {
      const roomType = subParam || this.options.roomType || 'Double';
      this.buildRoomInteriorModel(roomType);
      this.camera.position.set(11, 9, 12);
      if (this.controls) this.controls.target.set(0, 2.5, 0);
    }

    this.scene.add(this.currentMeshGroup);
    if (this.controls) this.controls.update();
  }

  // =========================================================================
  // 1. ARCHITECTURAL BUILDING EXTERIOR
  // =========================================================================
  buildBuildingModel() {
    const group = this.currentMeshGroup;

    // Architectural Materials
    const groundMat = new THREE.MeshStandardMaterial({ color: 0xDCE3DC, roughness: 0.9 });
    const stonePlazaMat = new THREE.MeshStandardMaterial({ color: 0xE5E1D8, roughness: 0.8 });
    const wallMainMat = new THREE.MeshStandardMaterial({ color: 0xF4F1E9, roughness: 0.6 });
    const wallAccentMat = new THREE.MeshStandardMaterial({ color: 0x202725, roughness: 0.4 });
    const bronzeTrimMat = new THREE.MeshStandardMaterial({ color: 0xA68A64, roughness: 0.3, metalness: 0.3 });
    const windowGlassMat = new THREE.MeshStandardMaterial({ color: 0x2b3834, roughness: 0.1, metalness: 0.6 });
    const foliageMat = new THREE.MeshStandardMaterial({ color: 0x4f6a54, roughness: 0.8 });

    // Ground & Landscaping
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    group.add(ground);

    const plaza = new THREE.Mesh(new THREE.BoxGeometry(32, 0.2, 24), stonePlazaMat);
    plaza.position.set(0, 0.1, 2);
    plaza.receiveShadow = true;
    group.add(plaza);

    // Central Residence Wing (3 floors)
    const mainWing = new THREE.Mesh(new THREE.BoxGeometry(18, 11, 10), wallMainMat);
    mainWing.position.set(0, 5.5, 0);
    mainWing.castShadow = true;
    mainWing.receiveShadow = true;
    group.add(mainWing);

    // North-West Resident Block
    const westWing = new THREE.Mesh(new THREE.BoxGeometry(8, 9, 14), wallMainMat);
    westWing.position.set(-11, 4.5, 2);
    westWing.castShadow = true;
    westWing.receiveShadow = true;
    group.add(westWing);

    // East Academic Lounge Wing
    const eastWing = new THREE.Mesh(new THREE.BoxGeometry(8, 8, 12), wallMainMat);
    eastWing.position.set(11, 4.0, 1);
    eastWing.castShadow = true;
    eastWing.receiveShadow = true;
    group.add(eastWing);

    // Architectural Roof Terraces & Bronze Parapets
    const roofMain = new THREE.Mesh(new THREE.BoxGeometry(18.4, 0.4, 10.4), bronzeTrimMat);
    roofMain.position.set(0, 11.2, 0);
    group.add(roofMain);

    const roofWest = new THREE.Mesh(new THREE.BoxGeometry(8.4, 0.3, 14.4), bronzeTrimMat);
    roofWest.position.set(-11, 9.15, 2);
    group.add(roofWest);

    // Entrance Portico with Charcoal Canopy
    const porticoCanopy = new THREE.Mesh(new THREE.BoxGeometry(8, 0.4, 4.5), wallAccentMat);
    porticoCanopy.position.set(0, 3.8, 6.5);
    porticoCanopy.castShadow = true;
    group.add(porticoCanopy);

    // Columns
    [-3.2, 3.2].forEach(x => {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 3.8, 16), bronzeTrimMat);
      col.position.set(x, 1.9, 8.2);
      col.castShadow = true;
      group.add(col);
    });

    // Glass Entrance Doors
    const door = new THREE.Mesh(new THREE.BoxGeometry(3.6, 2.8, 0.1), windowGlassMat);
    door.position.set(0, 1.4, 5.05);
    group.add(door);

    // Modern Rhythmic Window Grid
    const addWindowRow = (startY, count, spacing, xOffset, zPos) => {
      for (let i = 0; i < count; i++) {
        const x = xOffset - ((count - 1) * spacing) / 2 + i * spacing;
        const win = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.8, 0.15), windowGlassMat);
        win.position.set(x, startY, zPos);
        group.add(win);

        // Window frame accent
        const frame = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.08, 0.25), bronzeTrimMat);
        frame.position.set(x, startY - 0.9, zPos);
        group.add(frame);
      }
    };

    // Windows across floors 1, 2, 3
    [3.2, 6.4, 9.4].forEach(y => {
      addWindowRow(y, 6, 2.6, 0, 5.05); // Central
      addWindowRow(y - 0.5, 3, 2.4, -11, 9.05); // West
      if (y < 9) addWindowRow(y - 0.5, 3, 2.4, 11, 7.05); // East
    });

    // Landscaped Courtyard Hedges & Path
    [-6, 6].forEach(x => {
      const hedge = new THREE.Mesh(new THREE.BoxGeometry(2.5, 1.1, 7), foliageMat);
      hedge.position.set(x, 0.55, 9);
      hedge.castShadow = true;
      group.add(hedge);
    });
  }

  // =========================================================================
  // 2. FLOOR PLAN CUTAWAY
  // =========================================================================
  buildFloorCutawayModel() {
    const group = this.currentMeshGroup;
    const wallMat = new THREE.MeshStandardMaterial({ color: 0xF4F1E9, roughness: 0.7 });
    const floorMat = new THREE.MeshStandardMaterial({ color: 0xE5E1D8, roughness: 0.6 });
    const corridorMat = new THREE.MeshStandardMaterial({ color: 0xDCE3DC, roughness: 0.6 });
    const doorMat = new THREE.MeshStandardMaterial({ color: 0xA68A64, roughness: 0.4 });

    // Base Floor slab
    const slab = new THREE.Mesh(new THREE.BoxGeometry(26, 0.4, 16), floorMat);
    slab.position.set(0, 0.2, 0);
    slab.receiveShadow = true;
    group.add(slab);

    // Central Corridor
    const corridor = new THREE.Mesh(new THREE.BoxGeometry(24, 0.02, 3), corridorMat);
    corridor.position.set(0, 0.41, 0);
    group.add(corridor);

    // Outer Perimeter Low Cutaway Walls (Height = 2.4)
    const wallH = 2.2;
    const addWall = (w, h, d, x, y, z) => {
      const wall = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), wallMat);
      wall.position.set(x, y, z);
      wall.castShadow = true;
      wall.receiveShadow = true;
      group.add(wall);
    };

    // North & South perimeter walls
    addWall(26, wallH, 0.3, 0, wallH / 2 + 0.4, -7.8);
    addWall(26, wallH, 0.3, 0, wallH / 2 + 0.4, 7.8);
    // East & West perimeter walls
    addWall(0.3, wallH, 16, -12.8, wallH / 2 + 0.4, 0);
    addWall(0.3, wallH, 16, 12.8, wallH / 2 + 0.4, 0);

    // Room Partitions & Interactive Room Zones
    const roomDefs = [
      { no: "101", x: -8, z: -4.5, type: "Single", status: "Full", cap: 1, occ: 1 },
      { no: "102", x: 0, z: -4.5, type: "Double", status: "Available", cap: 2, occ: 1 },
      { no: "103", x: 8, z: -4.5, type: "Double", status: "Available", cap: 2, occ: 0 },
      { no: "104", x: -8, z: 4.5, type: "Triple", status: "Available", cap: 3, occ: 0 },
      { no: "105", x: 0, z: 4.5, type: "Triple", status: "Available", cap: 3, occ: 0 },
      { no: "106", x: 8, z: 4.5, type: "Dormitory", status: "Available", cap: 6, occ: 0 }
    ];

    // Dividing Walls
    [-4, 4].forEach(x => {
      addWall(0.2, wallH, 6, x, wallH / 2 + 0.4, -4.7);
      addWall(0.2, wallH, 6, x, wallH / 2 + 0.4, 4.7);
    });
    // Corridor boundary walls with door openings
    [-8, 0, 8].forEach(x => {
      // Small wall segments flanking doors
      addWall(2.6, wallH, 0.2, x - 2.5, wallH / 2 + 0.4, -1.5);
      addWall(2.6, wallH, 0.2, x + 2.5, wallH / 2 + 0.4, -1.5);
      addWall(2.6, wallH, 0.2, x - 2.5, wallH / 2 + 0.4, 1.5);
      addWall(2.6, wallH, 0.2, x + 2.5, wallH / 2 + 0.4, 1.5);
    });

    // Create Interactive Room Blocks
    roomDefs.forEach(r => {
      const roomTileMat = new THREE.MeshStandardMaterial({
        color: r.status === 'Full' ? 0xf0d9d6 : 0xe7eedf,
        roughness: 0.5
      });
      const tile = new THREE.Mesh(new THREE.BoxGeometry(7.2, 0.1, 5.8), roomTileMat);
      tile.position.set(r.x, 0.45, r.z);
      tile.userData = r;
      group.add(tile);
      this.clickableObjects.push(tile);

      // Mini furniture indicators inside cutaway rooms
      this.addMiniBeds(r.x, r.z, r.cap, r.occ);
    });
  }

  addMiniBeds(rx, rz, cap, occ) {
    const group = this.currentMeshGroup;
    const bedMat = new THREE.MeshStandardMaterial({ color: 0x202725 });
    const occBedMat = new THREE.MeshStandardMaterial({ color: 0xA68A64 });

    const num = Math.min(cap, 3);
    for (let i = 0; i < num; i++) {
      const bx = rx - 2 + i * 1.8;
      const bz = rz - 1.2;
      const mat = (i < occ) ? occBedMat : bedMat;
      const miniBed = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.5, 2.2), mat);
      miniBed.position.set(bx, 0.7, bz);
      group.add(miniBed);
    }
  }

  // =========================================================================
  // 3. REALISTIC ROOM INTERIOR
  // =========================================================================
  buildRoomInteriorModel(roomType = 'Double') {
    const group = this.currentMeshGroup;

    // Materials
    const floorWoodMat = new THREE.MeshStandardMaterial({ color: 0xd6cbb8, roughness: 0.5 });
    const wallPlasterMat = new THREE.MeshStandardMaterial({ color: 0xF4F1E9, roughness: 0.8 });
    const woodFurnitureMat = new THREE.MeshStandardMaterial({ color: 0x6e563d, roughness: 0.4 });
    const linenMat = new THREE.MeshStandardMaterial({ color: 0x3d4744, roughness: 0.7 });
    const bronzeMetalMat = new THREE.MeshStandardMaterial({ color: 0xA68A64, roughness: 0.3, metalness: 0.4 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x8aa4a8, roughness: 0.1, metalness: 0.8, transparent: true, opacity: 0.6 });

    const roomW = 14;
    const roomH = 7.5;
    const roomD = 12;

    // Floor
    const floor = new THREE.Mesh(new THREE.BoxGeometry(roomW, 0.3, roomD), floorWoodMat);
    floor.position.set(0, -0.15, 0);
    floor.receiveShadow = true;
    group.add(floor);

    // Back Wall
    const backWall = new THREE.Mesh(new THREE.BoxGeometry(roomW, roomH, 0.3), wallPlasterMat);
    backWall.position.set(0, roomH / 2, -roomD / 2);
    backWall.receiveShadow = true;
    group.add(backWall);

    // Left Wall with Large Window
    const leftWall1 = new THREE.Mesh(new THREE.BoxGeometry(0.3, roomH, 3), wallPlasterMat);
    leftWall1.position.set(-roomW / 2, roomH / 2, -4.5);
    group.add(leftWall1);

    const leftWall2 = new THREE.Mesh(new THREE.BoxGeometry(0.3, roomH, 3), wallPlasterMat);
    leftWall2.position.set(-roomW / 2, roomH / 2, 4.5);
    group.add(leftWall2);

    // Architectural Window with Sunlight
    const windowGlass = new THREE.Mesh(new THREE.BoxGeometry(0.1, 4.5, 6), glassMat);
    windowGlass.position.set(-roomW / 2, 3.8, 0);
    group.add(windowGlass);

    // Window Frame
    const windowFrame = new THREE.Mesh(new THREE.BoxGeometry(0.2, 4.8, 6.2), bronzeMetalMat);
    windowFrame.position.set(-roomW / 2, 3.8, 0);
    group.add(windowFrame);

    // Right Wall (Wardrobes & Shelves)
    const rightWall = new THREE.Mesh(new THREE.BoxGeometry(0.3, roomH, roomD), wallPlasterMat);
    rightWall.position.set(roomW / 2, roomH / 2, 0);
    rightWall.receiveShadow = true;
    group.add(rightWall);

    // Helper: Add Student Study Desk + Ergonomic Chair
    const addStudyStation = (x, z, rotY = 0) => {
      const deskGroup = new THREE.Group();
      // Desk Top
      const top = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.15, 1.8), woodFurnitureMat);
      top.position.set(0, 2.3, 0);
      top.castShadow = true;
      deskGroup.add(top);
      // Legs
      [[-1.5, -0.7], [1.5, -0.7], [-1.5, 0.7], [1.5, 0.7]].forEach(([lx, lz]) => {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.3), bronzeMetalMat);
        leg.position.set(lx, 1.15, lz);
        leg.castShadow = true;
        deskGroup.add(leg);
      });
      // Modern Desk Lamp
      const lampBase = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.05), bronzeMetalMat);
      lampBase.position.set(1.2, 2.4, -0.5);
      deskGroup.add(lampBase);
      const lampShade = new THREE.Mesh(new THREE.ConeGeometry(0.25, 0.3, 16), bronzeMetalMat);
      lampShade.position.set(1.2, 3.0, -0.5);
      lampShade.rotation.x = Math.PI / 4;
      deskGroup.add(lampShade);

      // Chair
      const chairSeat = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.1, 1.2), linenMat);
      chairSeat.position.set(0, 1.4, 0.8);
      chairSeat.castShadow = true;
      deskGroup.add(chairSeat);
      const chairBack = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.2, 0.1), linenMat);
      chairBack.position.set(0, 2.0, 1.35);
      deskGroup.add(chairBack);

      deskGroup.position.set(x, 0, z);
      deskGroup.rotation.y = rotY;
      group.add(deskGroup);
    };

    // Helper: Add Detailed Student Bed
    const addStudentBed = (x, z) => {
      const bedGroup = new THREE.Group();
      // Wooden Frame
      const frame = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.7, 6.4), woodFurnitureMat);
      frame.position.set(0, 0.35, 0);
      frame.castShadow = true;
      frame.receiveShadow = true;
      bedGroup.add(frame);
      // Mattress & Linen
      const mattress = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.5, 6.2), linenMat);
      mattress.position.set(0, 0.8, 0);
      mattress.castShadow = true;
      bedGroup.add(mattress);
      // Pillow
      const pillowMat = new THREE.MeshStandardMaterial({ color: 0xF4F1E9, roughness: 0.9 });
      const pillow = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.25, 1.2), pillowMat);
      pillow.position.set(0, 1.1, -2.2);
      bedGroup.add(pillow);
      // Headboard
      const headboard = new THREE.Mesh(new THREE.BoxGeometry(3.6, 2.2, 0.2), woodFurnitureMat);
      headboard.position.set(0, 1.1, -3.2);
      headboard.castShadow = true;
      bedGroup.add(headboard);

      bedGroup.position.set(x, 0, z);
      group.add(bedGroup);
    };

    // Helper: Add Wardrobe
    const addWardrobe = (x, z) => {
      const robe = new THREE.Mesh(new THREE.BoxGeometry(2.8, 6.0, 2.0), woodFurnitureMat);
      robe.position.set(x, 3.0, z);
      robe.castShadow = true;
      group.add(robe);
      // Handle trims
      const handle = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.8, 0.06), bronzeMetalMat);
      handle.position.set(x - 0.2, 3.0, z + 1.05);
      group.add(handle);
    };

    // Configure layout based on roomType
    if (roomType === 'Single') {
      addStudentBed(0, -1.8);
      addStudyStation(-3.8, 3.2, Math.PI / 2);
      addWardrobe(4.8, -3.8);
    } else if (roomType === 'Triple') {
      addStudentBed(-3.8, -1.8);
      addStudentBed(0, -1.8);
      addStudentBed(3.8, -1.8);
      addStudyStation(-4.0, 3.4);
      addStudyStation(0, 3.4);
      addStudyStation(4.0, 3.4);
      addWardrobe(5.6, -3.8);
    } else { // 'Double' default
      addStudentBed(-3.2, -1.8);
      addStudentBed(3.2, -1.8);
      addStudyStation(-3.2, 3.2);
      addStudyStation(3.2, 3.2);
      addWardrobe(5.6, -3.8);
    }
  }

  // Interaction: Raycasting on click
  onPointerDown(event) {
    if (this.clickableObjects.length === 0) return;
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.clickableObjects);

    if (intersects.length > 0) {
      const hitObj = intersects[0].object;
      if (hitObj.userData && this.options.onRoomSelect) {
        this.options.onRoomSelect(hitObj.userData);
      }
    }
  }

  onWindowResize() {
    if (!this.container) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (this.controls) this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

// Global factory helper
window.initHostel3D = function(containerId, options) {
  return new Hostel3DViewer(containerId, options);
};

