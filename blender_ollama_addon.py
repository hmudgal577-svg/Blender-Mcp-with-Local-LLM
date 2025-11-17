bl_info = {
    "name": "DeepSeek Robotics Assistant - FIXED",
    "author": "Fixed Version", 
    "version": (3, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > DeepSeek",
    "description": "AI Robotics modeling - All errors fixed",
    "category": "3D View",
}

import bpy
import json
import re
import ast
import math
import time
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel

# Check if requests is available
try:
    import requests
    REQUESTS_AVAILABLE = True
    print("✅ requests module loaded")
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ Install requests: pip install requests")


class DEEPSEEK_OT_test_connection(Operator):
    """Test Ollama connection"""
    bl_idname = "deepseek.test_connection"
    bl_label = "Test Connection"
    
    def execute(self, context):
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests not installed")
            return {'CANCELLED'}
            
        model = context.scene.deepseek_model
        
        try:
            print("\n" + "="*60)
            print("TESTING OLLAMA CONNECTION")
            print("="*60)
            
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            print("✅ Ollama server running")
            
            data = response.json()
            if 'models' in data:
                print(f"\n📦 Available models:")
                for m in data['models']:
                    print(f"   - {m['name']}")
            
            print(f"\n2️⃣ Testing model: {model}")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": "Say 'test'",
                    "stream": False,
                    "options": {"num_predict": 10}
                },
                timeout=15
            )
            response.raise_for_status()
            print("✅ Model responding")
            
            self.report({'INFO'}, f"✅ Connected to {model}")
            print("="*60 + "\n")
            
        except requests.exceptions.ConnectionError:
            self.report({'ERROR'}, "❌ Start Ollama: ollama serve")
            print("\n❌ Ollama not running!")
            return {'CANCELLED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            print(f"❌ Error: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class DEEPSEEK_OT_execute(Operator):
    """Execute AI command"""
    bl_idname = "deepseek.execute"
    bl_label = "Execute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests module not installed")
            return {'CANCELLED'}
        
        prompt = context.scene.deepseek_prompt
        model = context.scene.deepseek_model
        debug_mode = context.scene.deepseek_debug_mode
        use_fallback = context.scene.deepseek_use_fallback

        print("\n" + "="*60)
        print(f"🚀 EXECUTE: {prompt}")
        print(f"Model: {model} | Debug: {debug_mode} | Fallback: {use_fallback}")
        print("="*60)

        if not prompt:
            self.report({'WARNING'}, "Enter a command")
            return {'CANCELLED'}

        try:
            start_time = time.time()
            
            # Use fallback or AI
            if use_fallback:
                print("🔄 Using fallback code (AI bypassed)")
                code = self.get_fallback_code(prompt)
            else:
                self.report({'INFO'}, "Generating with AI...")
                code = self.generate_ai_code(prompt, model, context)
            
            generation_time = time.time() - start_time
            print(f"⏱️  Time: {generation_time:.2f}s")
            
            if not code or len(code.strip()) < 20:
                print("⚠️ AI failed, using fallback")
                code = self.get_fallback_code(prompt)

            if debug_mode:
                print("\n" + "="*60)
                print("GENERATED CODE:")
                print("="*60)
                print(code)
                print("="*60 + "\n")

            # Validate syntax
            syntax_error = self.validate_syntax(code)
            if syntax_error:
                print(f"❌ Syntax error: {syntax_error}")
                self.report({'ERROR'}, f"Syntax error: {syntax_error}")
                context.scene.deepseek_last_code = f"# ERROR: {syntax_error}\n\n{code}"
                return {'CANCELLED'}

            # Execute
            self.report({'INFO'}, "Executing...")
            exec_globals = {
                "bpy": bpy,
                "math": math,
                "Vector": __import__("mathutils").Vector,
                "Matrix": __import__("mathutils").Matrix,
                "Euler": __import__("mathutils").Euler,
            }
            
            try:
                exec(code, exec_globals)
                print("✅ Execution successful")
            except Exception as e:
                print(f"❌ Execution error: {e}")
                import traceback
                traceback.print_exc()
                self.report({'ERROR'}, f"Execution error: {str(e)[:50]}")
                context.scene.deepseek_last_code = f"# EXEC ERROR: {e}\n\n{code}"
                return {'CANCELLED'}

            # Apply materials
            if context.scene.deepseek_auto_material:
                self.apply_materials()

            context.scene.deepseek_last_code = code
            context.scene.deepseek_last_time = f"{generation_time:.2f}s"
            self.report({'INFO'}, f"✅ Created in {generation_time:.2f}s")

        except Exception as e:
            print(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Error: {str(e)[:50]}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def apply_materials(self):
        """Apply materials to objects"""
        try:
            colors = [
                (0.7, 0.7, 0.8, 1.0),  # Aluminum
                (0.3, 0.3, 0.4, 1.0),  # Steel
                (0.8, 0.1, 0.1, 1.0),  # Red
                (0.1, 0.5, 0.8, 1.0),  # Blue
                (0.9, 0.7, 0.1, 1.0),  # Gold
                (0.2, 0.6, 0.3, 1.0),  # Green
            ]
            
            idx = 0
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and not obj.data.materials:
                    mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
                    mat.use_nodes = True
                    bsdf = mat.node_tree.nodes.get("Principled BSDF")
                    if bsdf:
                        bsdf.inputs["Base Color"].default_value = colors[idx % len(colors)]
                        bsdf.inputs["Metallic"].default_value = 0.7
                        bsdf.inputs["Roughness"].default_value = 0.3
                    obj.data.materials.append(mat)
                    idx += 1
            print(f"✅ Materials applied: {idx}")
        except Exception as e:
            print(f"Material error: {e}")

    def validate_syntax(self, code):
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return str(e)

    def generate_ai_code(self, prompt, model, context):
        """Generate code with AI"""
        
        system_prompt = f"""Generate Blender Python code for: {prompt}

Requirements:
- Start with: import bpy
- Clear scene first
- Create geometry with bpy.ops or bpy.data
- Link objects to bpy.context.collection
- Use Blender 3.0+ API
- Return ONLY code, no explanations

Code structure:
```python
import bpy
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
# Your code here
```

Generate complete code now:"""

        try:
            print("🔄 Connecting to Ollama...")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": system_prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 1500,
                    }
                },
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            print("✅ Streaming response...")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return ""

        code = ""
        token_count = 0
        last_update = time.time()
        
        try:
            for line in response.iter_lines():
                if not line:
                    continue
                    
                try:
                    data = json.loads(line.decode("utf-8"))
                    
                    if "response" in data:
                        code += data["response"]
                        token_count += 1
                        
                        # Progress update every 3 seconds
                        if time.time() - last_update > 3:
                            print(f"📝 Tokens: {token_count}")
                            last_update = time.time()
                    
                    if data.get("done", False):
                        print(f"✅ Total tokens: {token_count}")
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            return code if code.strip() else ""

        # Extract code from response
        extracted = self.extract_code(code)
        
        if not extracted or len(extracted) < 30:
            print("⚠️ Extraction failed")
            return code
        
        print(f"📊 Code length: {len(extracted)} chars")
        return extracted

    def extract_code(self, text):
        """Extract code from AI response"""
        
        if not text or not text.strip():
            return ""
        
        # Try python code blocks
        pattern1 = r'```python\s*(.*?)\s*```'
        matches = re.findall(pattern1, text, re.DOTALL | re.IGNORECASE)
        if matches:
            longest = max(matches, key=len).strip()
            print("✅ Extracted from python block")
            return longest
        
        # Try generic code blocks
        pattern2 = r'```\s*(.*?)\s*```'
        matches = re.findall(pattern2, text, re.DOTALL)
        if matches:
            for block in matches:
                if 'import bpy' in block or 'bpy.' in block:
                    print("✅ Extracted from code block")
                    return block.strip()
        
        # Extract code-like lines
        lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if (stripped.startswith(('import ', 'from ', 'bpy.', 'def ', 'class ', 'for ', 'if ')) or
                ('=' in stripped and 'bpy' in stripped)):
                lines.append(line.rstrip())
        
        if lines:
            result = '\n'.join(lines)
            print("✅ Extracted from lines")
            return result
        
        return ""

    def get_fallback_code(self, prompt):
        """Smart fallback code based on prompt keywords"""
        
        prompt_lower = prompt.lower()
        
        # Detect object type from prompt
        if any(word in prompt_lower for word in ['robot', 'arm', 'articulated', 'gripper', 'manipulator']):
            return self.get_robot_arm_code()
        elif any(word in prompt_lower for word in ['table', 'desk', 'furniture']):
            return self.get_table_code()
        elif any(word in prompt_lower for word in ['chair', 'seat', 'stool']):
            return self.get_chair_code()
        elif any(word in prompt_lower for word in ['cube', 'box', 'block']):
            return self.get_cubes_code(prompt)
        elif any(word in prompt_lower for word in ['sphere', 'ball', 'orb']):
            return self.get_spheres_code(prompt)
        elif any(word in prompt_lower for word in ['cylinder', 'pipe', 'tube']):
            return self.get_cylinders_code(prompt)
        elif any(word in prompt_lower for word in ['house', 'building', 'structure']):
            return self.get_house_code()
        elif any(word in prompt_lower for word in ['tree', 'plant']):
            return self.get_tree_code()
        elif any(word in prompt_lower for word in ['car', 'vehicle', 'automobile']):
            return self.get_car_code()
        else:
            # Generic geometric shape
            return self.get_generic_code(prompt)
    
    def get_robot_arm_code(self):
        """Robot arm fallback"""
        return """import bpy
from mathutils import Vector

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating Robot Arm...")

# Base
bpy.ops.mesh.primitive_cylinder_add(radius=2.0, depth=0.8, location=(0, 0, 0.4))
bpy.context.active_object.name = "Base"

# Armature
bpy.ops.object.armature_add(location=(0, 0, 0.8))
arm_obj = bpy.context.active_object
arm_obj.name = "RobotArmature"
bpy.ops.object.mode_set(mode='EDIT')
bones = arm_obj.data.edit_bones
if bones:
    bones.remove(bones[0])

# 6 joints
b1 = bones.new("Joint1"); b1.head = Vector((0,0,0.8)); b1.tail = Vector((0,0,2.0))
b2 = bones.new("Joint2"); b2.head = b1.tail; b2.tail = Vector((0,0,3.2)); b2.parent = b1
b3 = bones.new("Joint3"); b3.head = b2.tail; b3.tail = Vector((0,0,4.4)); b3.parent = b2
b4 = bones.new("Joint4"); b4.head = b3.tail; b4.tail = Vector((0,0,5.2)); b4.parent = b3
b5 = bones.new("Joint5"); b5.head = b4.tail; b5.tail = Vector((0,0,5.8)); b5.parent = b4
b6 = bones.new("Joint6"); b6.head = b5.tail; b6.tail = Vector((0,0,6.3)); b6.parent = b5
hand = bones.new("Hand"); hand.head = b6.tail; hand.tail = Vector((0,0,6.8)); hand.parent = b6

for i in range(5):
    x = i * 0.25 - 0.5
    f = bones.new(f"Finger{i+1}"); f.head = Vector((x,0.3,6.8)); f.tail = Vector((x,0.3,7.4)); f.parent = hand

bpy.ops.object.mode_set(mode='OBJECT')

# Segments
for i, z in enumerate([1.4, 2.6, 3.8, 4.8, 5.5, 6.05]):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=1, location=(0,0,z))
    bpy.context.active_object.name = f"Segment{i+1}"

# Joints
for i, z in enumerate([0.8, 2.0, 3.2, 4.4, 5.2, 5.8, 6.3]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(0,0,z))
    bpy.context.active_object.name = f"Joint{i+1}"

# Hand
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,6.8))
bpy.context.active_object.name = "Palm"
bpy.context.active_object.scale = (1.2, 0.7, 0.4)

for i in range(5):
    x = i * 0.25 - 0.5
    bpy.ops.mesh.primitive_cube_add(size=0.15, location=(x,0.3,7.1))
    bpy.context.active_object.name = f"Finger{i+1}"
    bpy.context.active_object.scale = (0.7, 1, 2)

print("✅ Robot arm complete!")
"""
    
    def get_table_code(self):
        """Table fallback"""
        return """import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating table...")

# Table top
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
top = bpy.context.active_object
top.name = "TableTop"
top.scale = (1, 0.6, 0.05)

# 4 legs
positions = [(1.5, 1, 1), (-1.5, 1, 1), (1.5, -1, 1), (-1.5, -1, 1)]
for i, pos in enumerate(positions):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=pos)
    leg = bpy.context.active_object
    leg.name = f"Leg{i+1}"
    leg.scale = (1, 1, 5)

print("✅ Table complete!")
"""
    
    def get_chair_code(self):
        """Chair fallback"""
        return """import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating chair...")

# Seat
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1))
seat = bpy.context.active_object
seat.name = "Seat"
seat.scale = (1, 1, 0.1)

# Back
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.45, 1.5))
back = bpy.context.active_object
back.name = "Back"
back.scale = (1, 0.1, 1)

# 4 legs
positions = [(0.4, 0.4, 0.5), (-0.4, 0.4, 0.5), (0.4, -0.4, 0.5), (-0.4, -0.4, 0.5)]
for i, pos in enumerate(positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=pos)
    bpy.context.active_object.name = f"Leg{i+1}"

print("✅ Chair complete!")
"""
    
    def get_cubes_code(self, prompt):
        """Multiple cubes"""
        import re
        num_match = re.search(r'\d+', prompt)
        num = int(num_match.group()) if num_match else 5
        num = min(num, 20)  # Limit to 20
        
        return f"""import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating {num} cubes...")

for i in range({num}):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 1.5, 0, 0.5))
    bpy.context.active_object.name = f"Cube_{{i+1}}"

print("✅ Cubes complete!")
"""
    
    def get_spheres_code(self, prompt):
        """Multiple spheres"""
        import re
        num_match = re.search(r'\d+', prompt)
        num = int(num_match.group()) if num_match else 5
        num = min(num, 20)
        
        return f"""import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating {num} spheres...")

for i in range({num}):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(i * 1.2, 0, 0.5))
    bpy.context.active_object.name = f"Sphere_{{i+1}}"

print("✅ Spheres complete!")
"""
    
    def get_cylinders_code(self, prompt):
        """Multiple cylinders"""
        import re
        num_match = re.search(r'\d+', prompt)
        num = int(num_match.group()) if num_match else 5
        num = min(num, 20)
        
        return f"""import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating {num} cylinders...")

for i in range({num}):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=2, location=(i * 1.5, 0, 1))
    bpy.context.active_object.name = f"Cylinder_{{i+1}}"

print("✅ Cylinders complete!")
"""
    
    def get_house_code(self):
        """Simple house"""
        return """import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating house...")

# Walls
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
walls = bpy.context.active_object
walls.name = "Walls"
walls.scale = (1, 1, 0.5)

# Roof
bpy.ops.mesh.primitive_cone_add(radius1=3, depth=2, location=(0, 0, 5))
roof = bpy.context.active_object
roof.name = "Roof"
roof.rotation_euler[0] = 0

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.1, 1))
door = bpy.context.active_object
door.name = "Door"
door.scale = (0.5, 0.1, 1)

print("✅ House complete!")
"""
    
    def get_tree_code(self):
        """Simple tree"""
        return """import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating tree...")

# Trunk
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=4, location=(0, 0, 2))
trunk = bpy.context.active_object
trunk.name = "Trunk"

# Leaves (3 spheres)
for i, z in enumerate([3.5, 4, 4.5]):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1.2, location=(0, 0, z))
    leaves = bpy.context.active_object
    leaves.name = f"Leaves_{i+1}"

print("✅ Tree complete!")
"""
    
    def get_car_code(self):
        """Simple car"""
        return """import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating car...")

# Body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
body = bpy.context.active_object
body.name = "Body"
body.scale = (1.5, 0.6, 0.3)

# Cabin
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 1.2))
cabin = bpy.context.active_object
cabin.name = "Cabin"
cabin.scale = (0.6, 0.6, 0.4)

# 4 wheels
positions = [(1, 0.7, 0.3), (-1, 0.7, 0.3), (1, -0.7, 0.3), (-1, -0.7, 0.3)]
for i, pos in enumerate(positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.3, location=pos)
    wheel = bpy.context.active_object
    wheel.name = f"Wheel_{i+1}"
    wheel.rotation_euler[1] = 1.5708  # 90 degrees

print("✅ Car complete!")
"""
    
    def get_generic_code(self, prompt):
        """Generic fallback"""
        return f"""import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

print("Creating generic object for: {prompt}")

# Create a simple structure
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
bpy.context.active_object.name = "Base"

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 3))
bpy.context.active_object.name = "Top"

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(0, 0, 2))
bpy.context.active_object.name = "Middle"

print("✅ Generic object complete!")
"""


class DEEPSEEK_PT_panel(Panel):
    """Main panel"""
    bl_label = "🤖 DeepSeek Robotics"
    bl_idname = "DEEPSEEK_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DeepSeek'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Header
        box = layout.box()
        box.label(text="DeepSeek Robotics (Fixed)", icon='CONSOLE')
        
        # Model
        box = layout.box()
        box.label(text="Model:", icon='NETWORK_DRIVE')
        box.prop(scene, "deepseek_model", text="")
        box.operator("deepseek.test_connection", icon='PLUGIN')

        layout.separator()

        # Command
        box = layout.box()
        box.label(text="Command:", icon='TOOL_SETTINGS')
        box.prop(scene, "deepseek_prompt", text="")
        
        # Options
        row = box.row()
        row.prop(scene, "deepseek_use_fallback", text="Use Fallback (Guaranteed)")
        
        row = box.row()
        row.prop(scene, "deepseek_auto_material", text="Materials")
        row.prop(scene, "deepseek_debug_mode", text="Debug")

        # Execute
        row = layout.row()
        row.scale_y = 2.0
        
        if scene.deepseek_use_fallback:
            row.operator("deepseek.execute", icon='PLAY', text="🔧 Create (Fallback)")
        else:
            row.operator("deepseek.execute", icon='PLAY', text="🤖 Create (AI)")

        # Status
        if hasattr(scene, "deepseek_last_time") and scene.deepseek_last_time:
            layout.separator()
            box = layout.box()
            box.label(text=f"Last: {scene.deepseek_last_time}", icon='TIME')

        # Code preview
        if hasattr(scene, "deepseek_last_code") and scene.deepseek_last_code:
            layout.separator()
            box = layout.box()
            box.label(text="Code:", icon='TEXT')
            
            lines = scene.deepseek_last_code.split('\n')[:6]
            for line in lines:
                if len(line) > 50:
                    box.label(text=line[:47] + "...")
                else:
                    box.label(text=line)

        # Examples
        layout.separator()
        box = layout.box()
        box.label(text="Examples:", icon='LIGHT')
        col = box.column(align=True)
        col.label(text="• 'robot arm with gripper'")
        col.label(text="• 'simple table'")
        col.label(text="• 'mechanical joint'")


def register():
    bpy.utils.register_class(DEEPSEEK_OT_test_connection)
    bpy.utils.register_class(DEEPSEEK_OT_execute)
    bpy.utils.register_class(DEEPSEEK_PT_panel)

    bpy.types.Scene.deepseek_prompt = StringProperty(
        name="Prompt",
        description="Describe what to create",
        default="robot arm with 6 joints and gripper"
    )

    bpy.types.Scene.deepseek_model = EnumProperty(
        name="Model",
        items=[
            ('deepseek-r1:7b', "DeepSeek R1 7B", "Fast"),
            ('deepseek-r1:14b', "DeepSeek R1 14B", "Balanced"),
            ('deepseek-r1:latest', "DeepSeek R1 Latest", "Best"),
            ('deepseek-coder:6.7b', "DeepSeek Coder", "Code focus"),
        ],
        default='deepseek-r1:7b'
    )

    bpy.types.Scene.deepseek_use_fallback = BoolProperty(
        name="Use Fallback",
        description="Skip AI and use guaranteed working code",
        default=True
    )

    bpy.types.Scene.deepseek_auto_material = BoolProperty(
        name="Auto Material",
        default=True
    )

    bpy.types.Scene.deepseek_debug_mode = BoolProperty(
        name="Debug",
        default=True
    )

    bpy.types.Scene.deepseek_last_code = StringProperty(default="")
    bpy.types.Scene.deepseek_last_time = StringProperty(default="")


def unregister():
    bpy.utils.unregister_class(DEEPSEEK_OT_execute)
    bpy.utils.unregister_class(DEEPSEEK_OT_test_connection)
    bpy.utils.unregister_class(DEEPSEEK_PT_panel)

    del bpy.types.Scene.deepseek_prompt
    del bpy.types.Scene.deepseek_model
    del bpy.types.Scene.deepseek_use_fallback
    del bpy.types.Scene.deepseek_auto_material
    del bpy.types.Scene.deepseek_debug_mode
    del bpy.types.Scene.deepseek_last_code
    del bpy.types.Scene.deepseek_last_time


if __name__ == "__main__":
    register()
