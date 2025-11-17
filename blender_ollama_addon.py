bl_info = {
    "name": "Ollama AI Assistant (Qwen2.5-Coder)",
    "author": "Your Name",
    "version": (1, 3, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Ollama",
    "description": "Control Blender with Qwen2.5-Coder:3b via Ollama",
    "category": "3D View",
}

import bpy
import json
import re
import ast
import math
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty
from bpy.types import Operator, Panel

# Check if requests is available
try:
    import requests
    REQUESTS_AVAILABLE = True
    print("✅ requests module loaded successfully")
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ requests module not available - install with: pip install requests")


def clear_scene_safe():
    """Safely clear all objects regardless of context"""
    # Use bpy.data instead of operators (context-independent)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    print("✅ Scene cleared safely")


def ensure_view3d_context():
    """Ensure we have a valid 3D View context"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {
                            'window': window,
                            'screen': window.screen,
                            'area': area,
                            'region': region,
                        }
                        return override
    return None


class OLLAMA_OT_test_connection(Operator):
    """Test connection to Ollama server"""
    bl_idname = "ollama.test_connection"
    bl_label = "Test Connection"
    
    def execute(self, context):
        model = context.scene.ollama_model
        
        try:
            print("\n" + "="*60)
            print("TESTING OLLAMA CONNECTION")
            print("="*60)
            
            # Test 1: Server reachability
            print("1️⃣ Testing server at http://localhost:11434...")
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            print("✅ Server is reachable")
            
            # Show available models
            data = response.json()
            if 'models' in data:
                print(f"\n📦 Available models:")
                for m in data['models']:
                    print(f"   - {m['name']}")
            
            # Test 2: Generate simple code
            print(f"\n2️⃣ Testing code generation with {model}...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": "Write Python: print('hello')",
                    "stream": False,
                    "options": {"num_predict": 30}
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            generated = result.get('response', '')
            print(f"✅ Generated: {generated[:100]}...")
            
            if generated.strip():
                self.report({'INFO'}, f"✅ Connection successful! Model: {model}")
                print("\n✅ ALL TESTS PASSED")
            else:
                self.report({'WARNING'}, "Model responded but generated empty code")
                print("\n⚠️ Empty response - model may need configuration")
            
            print("="*60 + "\n")
            
        except requests.exceptions.ConnectionError:
            self.report({'ERROR'}, "❌ Cannot connect to Ollama - is it running?")
            print("\n❌ Connection failed. Run: ollama serve")
            print("="*60 + "\n")
            return {'CANCELLED'}
            
        except requests.exceptions.Timeout:
            self.report({'ERROR'}, "❌ Request timed out")
            print("\n❌ Timeout - server may be busy")
            print("="*60 + "\n")
            return {'CANCELLED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"❌ Error: {str(e)}")
            print(f"\n❌ Error: {e}")
            print("="*60 + "\n")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class OLLAMA_OT_execute(Operator):
    """Execute natural language command through Ollama"""
    bl_idname = "ollama.execute"
    bl_label = "Execute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check if requests module is available
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests module not installed. Install with: pip install requests")
            return {'CANCELLED'}
        
        prompt = context.scene.ollama_prompt
        model = context.scene.ollama_model
        debug_mode = context.scene.ollama_debug_mode
        max_tokens = context.scene.ollama_max_tokens

        print("\n" + "="*60)
        print("🚀 OLLAMA EXECUTE STARTED")
        print("="*60)
        print(f"Prompt: {prompt}")
        print(f"Model: {model}")
        print(f"Debug: {debug_mode}")
        print(f"Max Tokens: {max_tokens}")
        print("="*60 + "\n")

        if not prompt:
            self.report({'WARNING'}, "Please enter a command")
            return {'CANCELLED'}

        # Detect complexity level
        complexity = self.assess_complexity(prompt)
        if debug_mode:
            print(f"📊 Prompt complexity level: {complexity}")

        try:
            # 1️⃣ Generate code using Ollama
            self.report({'INFO'}, "Generating code...")
            print("\n🔄 Calling generate_code()...")
            
            code = self.generate_code(prompt, model, max_tokens, complexity)
            
            print(f"\n📦 generate_code() returned: {len(code) if code else 0} characters")

            if not code.strip():
                print("❌ Code is empty or whitespace only")
                self.report({'ERROR'}, "No valid code generated — check Ollama server")
                return {'CANCELLED'}

            if debug_mode:
                print("\n" + "="*60)
                print("RAW GENERATED CODE:")
                print("="*60)
                print(code)
                print("="*60 + "\n")

            # 2️⃣ Fix Blender API issues
            code = self.fix_blender_api(code)
            
            # 2.5️⃣ Extra pass for material fixes (critical for color errors)
            code = self.fix_material_errors(code)

            if debug_mode:
                print("\n" + "="*60)
                print("AFTER API FIXES:")
                print("="*60)
                print(code)
                print("="*60 + "\n")

            # 3️⃣ Validate syntax
            syntax_error = self.validate_syntax(code)
            if syntax_error:
                if debug_mode:
                    print(f"\n❌ SYNTAX ERROR:\n{syntax_error}")
                    print("\nPROBLEMATIC CODE:")
                    for i, line in enumerate(code.split('\n'), 1):
                        print(f"{i:3}: {line}")
                
                self.report({'ERROR'}, f"Syntax Error: {syntax_error}")
                context.scene.ollama_last_code = f"# SYNTAX ERROR:\n# {syntax_error}\n\n{code}"
                return {'CANCELLED'}

            # 4️⃣ Execute with proper context handling and error recovery
            self.report({'INFO'}, "Executing code...")
            exec_globals = {
                "bpy": bpy,
                "mathutils": __import__("mathutils"),
                "math": math,
            }
            
            try:
                exec(code, exec_globals)
            except AttributeError as e:
                error_str = str(e)
                print(f"\n⚠️ AttributeError caught: {error_str}")
                
                # Try to fix common attribute errors
                if "add_child" in error_str or "set_parent" in error_str:
                    print("🔧 Attempting to fix parent/child relationship code...")
                    code = self.fix_parent_child_errors(code)
                    if debug_mode:
                        print("\n🔧 FIXED CODE:")
                        print(code)
                    exec(code, exec_globals)
                elif "world" in error_str or "BlendData" in error_str:
                    print("🔧 Attempting to fix material/world errors...")
                    code = self.fix_material_errors(code)
                    if debug_mode:
                        print("\n🔧 FIXED CODE:")
                        print(code)
                    exec(code, exec_globals)
                else:
                    raise

            # 5️⃣ Post-execution cleanup
            if context.scene.ollama_auto_material:
                self.apply_auto_materials(context)
            
            # 5.5️⃣ Auto-switch to Material Preview if materials were added
            if 'materials.new' in code or 'Base Color' in code:
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                space.shading.type = 'MATERIAL'
                                print("✅ Switched to Material Preview mode")
                                break

            # Save last generated code
            context.scene.ollama_last_code = code
            self.report({'INFO'}, f"✅ Executed: {prompt}")

        except requests.exceptions.ConnectionError:
            self.report({'ERROR'}, "Ollama server not reachable — start it with 'ollama serve'")
            return {'CANCELLED'}

        except SyntaxError as e:
            self.report({'ERROR'}, f"Python Syntax Error: {e}")
            if debug_mode:
                import traceback
                traceback.print_exc()
            return {'CANCELLED'}

        except Exception as e:
            error_msg = str(e)
            if debug_mode:
                print(f"\n❌ EXECUTION ERROR:\n{error_msg}")
                import traceback
                traceback.print_exc()
            
            self.report({'ERROR'}, f"Execution Error: {error_msg}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def assess_complexity(self, prompt):
        """Assess prompt complexity to adjust generation parameters"""
        prompt_lower = prompt.lower()
        
        complexity_keywords = {
            'complex': ['rigging', 'rig', 'articulated', 'armature', 'bones', 'joints', 
                       'animate', 'animation', 'constraint', 'ik', 'fk', 'skeleton'],
            'moderate': ['multiple', 'several', 'array', 'pattern', 'scene', 'material',
                        'texture', 'modifier', 'subdivision'],
            'simple': ['create', 'add', 'make', 'cube', 'sphere', 'cylinder']
        }
        
        # Count complexity indicators
        complex_count = sum(1 for kw in complexity_keywords['complex'] if kw in prompt_lower)
        moderate_count = sum(1 for kw in complexity_keywords['moderate'] if kw in prompt_lower)
        
        if complex_count >= 2:
            return 'complex'
        elif complex_count >= 1 or moderate_count >= 2:
            return 'moderate'
        else:
            return 'simple'

    def apply_auto_materials(self, context):
        """Apply automatic materials to new objects"""
        try:
            for obj in context.selected_objects:
                if obj.type == 'MESH' and not obj.data.materials:
                    mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
                    mat.use_nodes = True
                    bsdf = mat.node_tree.nodes.get("Principled BSDF")
                    if bsdf:
                        # Random-ish color based on object name
                        import hashlib
                        hash_val = int(hashlib.md5(obj.name.encode()).hexdigest()[:6], 16)
                        r = ((hash_val >> 16) & 0xFF) / 255.0
                        g = ((hash_val >> 8) & 0xFF) / 255.0
                        b = (hash_val & 0xFF) / 255.0
                        bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
                    obj.data.materials.append(mat)
        except Exception as e:
            print(f"Auto-material error: {e}")

    def validate_syntax(self, code):
        """Validate Python syntax before execution"""
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  Code: {e.text.strip()}"
            return error_msg
        except Exception as e:
            return str(e)

    def fix_parent_child_errors(self, code):
        """Fix common parent/child relationship errors"""
        # Replace add_child with proper parent setting
        code = re.sub(
            r'(\w+)\.add_child\s*\(\s*(\w+)\s*\)',
            r'\2.parent = \1',
            code
        )
        
        # Replace set_parent method calls
        code = re.sub(
            r'(\w+)\.set_parent\s*\(\s*(\w+)\s*\)',
            r'\1.parent = \2',
            code
        )
        
        return code
    
    def fix_material_errors(self, code):
        """Fix common material and world-related errors"""
        # Remove bpy.data.world references (AI hallucination)
        code = re.sub(r'bpy\.data\.world[^\n]*\n?', '', code)
        
        # Remove world.use_nodes or similar
        code = re.sub(r'world\.use_nodes[^\n]*\n?', '', code)
        code = re.sub(r'world\.node_tree[^\n]*\n?', '', code)
        
        # Fix incorrect material creation
        code = re.sub(
            r'material\s*=\s*bpy\.data\.materials\.get\([^)]+\)',
            'material = bpy.data.materials.new(name="Material")',
            code
        )
        
        # Fix broken/incomplete color assignments
        code = re.sub(
            r'inputs\[["\']Base\s+C[^"\']*["\'][^\(]*\((\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*(?:\s*,\s*\d+\.?\d*)?)\)',
            r'inputs["Base Color"].default_value = (\1)',
            code
        )
        
        # Fix RGB to RGBA
        def fix_color_input(match):
            input_part = match.group(1)
            r = match.group(2)
            g = match.group(3)
            b = match.group(4)
            return f'{input_part}.default_value = ({r}, {g}, {b}, 1.0)'
        
        code = re.sub(
            r'(inputs\[["\'][^"\']+["\']]\s*)\.\s*default_value\s*=\s*\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*\)',
            fix_color_input,
            code
        )
        
        code = re.sub(
            r'\.default_value\s*=\s*\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*\)',
            r'.default_value = (\1, \2, \3, 1.0)',
            code
        )
        
        code = re.sub(
            r'(inputs\[["\'][^"\']+["\']]\s*)\.\s*\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*(?:,\s*\d+\.?\d*)?\s*\)',
            r'\1.default_value = (\2, \3, \4, 1.0)',
            code
        )
        
        code = re.sub(
            r'(bsdf|mat)\.inputs\[["\']Base\s*C[^\]]*\]\s*\((\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*)\)',
            r'\1.inputs["Base Color"].default_value = (\2)',
            code
        )
        
        return code

    def fix_blender_api(self, code):
        """Fix common Blender API issues and ensure proper object linking"""
        
        # CRITICAL FIX: Use context-safe clearing method
        force_clear = """import bpy

# Context-safe scene clearing (works from any context)
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

"""
        
        # CRITICAL FIX: Ensure imports at the beginning
        imports_needed = []
        if 'math.' in code or 'math.pi' in code or 'math.cos' in code or 'math.sin' in code:
            if 'import math' not in code:
                imports_needed.append('import math')
        
        if 'Vector' in code or 'Euler' in code or 'mathutils' in code:
            if 'from mathutils import' not in code and 'import mathutils' not in code:
                imports_needed.append('from mathutils import Vector')
        
        # Add missing imports to force_clear
        if imports_needed:
            force_clear = force_clear.rstrip() + '\n' + '\n'.join(imports_needed) + '\n\n'
        
        # Remove old bpy.ops clearing attempts
        code = re.sub(r'bpy\.ops\.object\.select_all\([^)]*\)[^\n]*\n', '', code)
        code = re.sub(r'bpy\.ops\.object\.delete\([^)]*\)[^\n]*\n', '', code)
        
        if 'import bpy' in code:
            code = re.sub(r'^import bpy\s*\n', '', code, count=1, flags=re.MULTILINE)
        if imports_needed:
            for imp in imports_needed:
                if imp in code:
                    code = re.sub(rf'^{re.escape(imp)}\s*\n', '', code, count=1, flags=re.MULTILINE)
        
        code = force_clear + code
        
        # Fix old API calls
        code = re.sub(
            r'bpy\.context\.scene\.objects\.link\s*\(\s*([^)]+)\s*\)',
            r'bpy.context.collection.objects.link(\1)',
            code
        )
        
        # NEW FIX: Remove duplicate collection.objects.link calls
        lines = code.split('\n')
        seen_links = set()
        cleaned_lines = []
        
        for line in lines:
            # Check if this is a link statement
            link_match = re.search(r'(?:bpy\.context\.)?(?:scene|collection)\.objects\.link\((\w+)\)', line)
            if link_match:
                var_name = link_match.group(1)
                if var_name in seen_links:
                    print(f"🔧 Removing duplicate link for: {var_name}")
                    continue  # Skip this duplicate
                else:
                    seen_links.add(var_name)
            
            cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines)
        
        # Remove invalid enum values
        invalid_enums = [
            (r"type\s*=\s*['\"]JOINT['\"]", ""),
            (r",\s*type\s*=\s*['\"]JOINT['\"]", ""),
            (r"type\s*=\s*['\"]BONE['\"]", ""),
            (r"connect\s*=\s*['\"]AUTO['\"]", "connect=True"),
            (r"type\s*=\s*['\"]REVOLUTE['\"]", ""),
            (r"type\s*=\s*['\"]HINGE['\"]", ""),
        ]
        
        for pattern, replacement in invalid_enums:
            code = re.sub(pattern, replacement, code)
        
        # Remove fake operators
        fake_operators = [
            r'bpy\.ops\.rigging\.add\([^)]*\)',
            r'bpy\.ops\.rigging\.create\([^)]*\)',
            r'bpy\.ops\.bone\.add\([^)]*\)',
            r'bpy\.ops\.armature\.create\([^)]*\)',
            r'bpy\.ops\.joint\.add\([^)]*\)',
        ]
        
        for pattern in fake_operators:
            code = re.sub(pattern, '', code)
        
        # Fix parent/child relationships
        code = self.fix_parent_child_errors(code)
        
        # Clean up double commas
        code = re.sub(r',\s*,', ',', code)
        code = re.sub(r'\(\s*,', '(', code)
        code = re.sub(r',\s*\)', ')', code)
        
        # Remove empty lines
        lines = code.split('\n')
        code = '\n'.join(line for line in lines if line.strip() or not line)
        
        # FIXED: Ensure objects created with bpy.data are linked (prevent parent errors)
        lines = code.split('\n')
        new_lines = []
        linked_objects = {}  # CHANGED: Track object variable names and their line numbers
        objects_from_ops = set()  # Track objects created with bpy.ops
        in_edit_mode = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if 'mode_set' in line and 'EDIT' in line:
                in_edit_mode = True
            elif 'mode_set' in line and 'OBJECT' in line:
                in_edit_mode = False
            
            # Track objects created with bpy.ops (they're auto-linked)
            if 'bpy.ops.mesh.primitive_' in line or 'bpy.ops.object.' in line:
                # Check if result is assigned to a variable
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    ops_match = re.match(r'(\w+)\s*=\s*bpy\.context\.(?:active_object|object)', next_line)
                    if ops_match:
                        var_name = ops_match.group(1)
                        objects_from_ops.add(var_name)
                        print(f"📝 Tracking bpy.ops created object: {var_name}")
            
            # Check if this line is trying to link an object
            if 'collection.objects.link(' in line or 'scene.objects.link(' in line:
                link_match = re.search(r'\.objects\.link\((\w+)\)', line)
                if link_match:
                    var_name = link_match.group(1)
                    
                    # FIXED: Check if var_name is actually an object variable
                    # Skip if it looks like it's from a tracking set (not a real object)
                    if var_name in ['linked_objects', 'objects_from_ops', 'seen_links']:
                        print(f"🔧 Removing invalid link attempt on set variable: {var_name}")
                        continue
                    
                    # Skip if object was created with bpy.ops (already linked)
                    if var_name in objects_from_ops:
                        print(f"🔧 Removing unnecessary link for bpy.ops object: {var_name}")
                        continue
                    
                    # Skip if already linked
                    if var_name in linked_objects:
                        print(f"🔧 Skipping duplicate link for: {var_name}")
                        continue
                    else:
                        linked_objects[var_name] = i  # Store with line number
            
            new_lines.append(line)
            
            if in_edit_mode:
                continue
            
            # Auto-link objects created with bpy.data.objects.new (NOT bpy.ops)
            match = re.search(r'(\w+)\s*=\s*bpy\.data\.objects\.new\s*\(', line)
            if match:
                var_name = match.group(1)
                
                # FIXED: Validate that this is a real object variable name
                # Skip internal tracking variables
                if var_name in ['linked_objects', 'objects_from_ops', 'seen_links']:
                    print(f"⚠️ Skipping auto-link for internal variable: {var_name}")
                    continue
                
                # Only link if not already linked and not from bpy.ops
                if var_name not in linked_objects and var_name not in objects_from_ops:
                    # Check if next line already links it
                    next_line = lines[i + 1] if i + 1 < len(lines) else ""
                    if 'collection.objects.link' not in next_line and 'scene.objects.link' not in next_line:
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + f"bpy.context.collection.objects.link({var_name})")
                        linked_objects[var_name] = len(new_lines) - 1  # Store line number
                        print(f"✅ Auto-linking bpy.data object: {var_name}")
        
        code = '\n'.join(new_lines)
        
        # Handle armature patterns
        code = re.sub(
            r'(bpy\.ops\.object\.armature_add\([^)]*\))',
            r'\1\narm_obj = bpy.context.active_object',
            code
        )
        
        # Safe mode changes - wrap mode_set in try-except
        lines = code.split('\n')
        safe_lines = []
        for line in lines:
            if 'mode_set' in line and 'try:' not in line:
                indent = len(line) - len(line.lstrip())
                safe_lines.append(' ' * indent + 'try:')
                safe_lines.append(' ' * (indent + 4) + line.strip())
                safe_lines.append(' ' * indent + 'except RuntimeError:')
                safe_lines.append(' ' * (indent + 4) + 'pass  # Context not available')
            else:
                safe_lines.append(line)
        
        code = '\n'.join(safe_lines)
        
        # Balance brackets
        code = self.fix_syntax_errors(code)
        
        return code

    def fix_syntax_errors(self, code):
        """Fix unclosed brackets and parentheses"""
        
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            if stripped and ('bpy.ops.' in stripped or 'bpy.data.' in stripped):
                open_paren = line.count('(')
                close_paren = line.count(')')
                
                if open_paren > close_paren:
                    missing = open_paren - close_paren
                    line = line.rstrip() + (')' * missing)
            
            fixed_lines.append(line)
        
        code = '\n'.join(fixed_lines)
        
        # Global bracket balancing
        bracket_count = code.count('[') - code.count(']')
        paren_count = code.count('(') - code.count(')')
        brace_count = code.count('{') - code.count('}')
        
        if bracket_count > 0:
            code += '\n' + (']' * bracket_count)
        if paren_count > 0:
            code += '\n' + (')' * paren_count)
        if brace_count > 0:
            code += '\n' + ('}' * brace_count)
        
        return code

    def generate_code(self, prompt, model, max_tokens, complexity):
        """Generate Blender code optimized for Qwen2.5-Coder:3b"""
        
        blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
        
        # Simplified, concise system prompt for smaller model
        if complexity == 'complex':
            system_msg = f"""Generate ONLY executable Python code. NO explanations, NO comments about what the code does, NO markdown except code blocks.

Start immediately with:
```python
import bpy
import math

# Context-safe clearing (works everywhere)
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# code here
```

Rules:
- Use bpy.ops for objects
- Materials: bsdf.inputs["Base Color"].default_value=(R,G,B,1.0)
- Parent: child.parent = parent_obj

{prompt}

```python"""
        
        elif complexity == 'moderate':
            system_msg = f"""Generate executable Python code only. NO text explanations.

```python
import bpy
import math

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# code
```

{prompt}

```python"""
        
        else:  # simple
            system_msg = f"""Python code only. NO explanations.

```python
import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
```

{prompt}

```python"""

        # Adjust token limits for 3B model (smaller limits for efficiency)
        token_limit = {
            'complex': min(max_tokens, 800),  # Cap at 800 for 3B
            'moderate': min(max_tokens, 500),
            'simple': min(max_tokens // 2, 300)
        }[complexity]

        try:
            print(f"🔄 Connecting to Ollama at http://localhost:11434...")
            print(f"📝 Model: {model}")
            print(f"🎯 Complexity: {complexity}")
            print(f"📊 Max tokens: {token_limit}")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": system_msg,
                    "stream": True,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": token_limit,
                        "repeat_penalty": 1.1,
                        "stop": ["```\n\n", "User:", "Request:", "Task:"]
                    }
                },
                stream=True,
                timeout=90
            )
            response.raise_for_status()
            print("✅ Connected to Ollama successfully")
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print("💡 Make sure Ollama is running with: ollama serve")
            return ""
        except requests.exceptions.Timeout:
            print("❌ Request timed out after 90 seconds")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return ""

        code = ""
        token_count = 0
        
        try:
            print("📥 Receiving streamed response...")
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        chunk = data["response"]
                        code += chunk
                        token_count += 1
                        
                        if token_count % 50 == 0:
                            print(f"   ...received {token_count} tokens")
                    
                    if data.get("done", False):
                        print(f"✅ Generation complete ({token_count} tokens)")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error on line: {line[:100]}")
                    continue
                    
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            import traceback
            traceback.print_exc()
            return ""

        if not code.strip():
            print("❌ No code generated - empty response from Ollama")
            return ""
        
        print(f"\n📝 RAW CODE BEFORE EXTRACTION ({len(code)} chars):")
        print("=" * 60)
        print(code[:500])
        print("=" * 60)

        code = self.extract_code(code)
        
        if not code.strip():
            print("❌ No valid code after extraction")
            return ""
        
        return code.strip()

    def extract_code(self, text):
        """Extract clean Python code from AI response"""
        
        if not text or not text.strip():
            print("⚠️ extract_code: Input text is empty")
            return ""
        
        print(f"\n🔍 EXTRACTING CODE FROM:")
        print("=" * 60)
        print(text[:500])
        print("=" * 60)
        
        original_text = text
        
        # CRITICAL: Remove common AI preambles
        preamble_patterns = [
            r'^.*?(?:here\s+is|below\s+is|here\'s).*?(?:script|code).*?:?\s*',
            r'^.*?(?:certainly|sure|ok|alright).*?:?\s*',
            r'^.*?(?:i\'ll|let me).*?(?:create|generate|write).*?:?\s*',
        ]
        
        for pattern in preamble_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove markdown code blocks
        if "```python" in text:
            match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
                print("✅ Extracted from ```python block")
        elif "```" in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
                print("✅ Extracted from ``` block")
        
        lines = text.split('\n')
        code_lines = []
        found_import = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines before code starts
            if not code_lines and not stripped:
                continue
            
            # Skip lines that are clearly not code
            if not found_import and stripped and not stripped.startswith(('import', 'from', '#', 'bpy')):
                # Check if line contains conversational text
                if any(word in stripped.lower() for word in 
                    ['certainly', 'sure', 'here', 'below', 'script', 'following', 
                     'this will', 'creates', 'demonstrates']):
                    continue
            
            # Mark that we've found actual code
            if stripped.startswith(('import', 'from')):
                found_import = True
            
            # Skip explanatory comments
            if stripped.startswith('#') and any(word in stripped.lower() 
                for word in ['this', 'here', 'note:', 'explanation', 'example:', 
                            'below', 'above', 'script', 'code']):
                continue
            
            # Stop at ending phrases
            if any(phrase in stripped.lower() for phrase in 
                ['let me know', 'hope this', 'feel free', 'this will create', 
                 'you can', 'try this', 'this should', 'if you', 'explanation:']):
                break
            
            # Only add line if we've found imports or it's actual code
            if found_import or stripped.startswith(('import', 'from', 'bpy', '#')):
                code_lines.append(line)
        
        result = '\n'.join(code_lines).strip()
        
        # If still no valid code, try to find first import statement
        if not result or 'import' not in result:
            print("⚠️ No imports found, searching for code block...")
            # Look for first occurrence of 'import bpy'
            import_match = re.search(r'(import bpy.*)', original_text, re.DOTALL | re.IGNORECASE)
            if import_match:
                result = import_match.group(1)
                # Clean up after finding import
                result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)  # Remove excessive newlines
                print("✅ Found code starting from 'import bpy'")
        
        if not result:
            print("⚠️ No code after extraction, returning original stripped text")
            result = original_text.strip()
        
        print(f"\n✅ FINAL EXTRACTED CODE ({len(result)} chars):")
        print("=" * 60)
        print(result[:300])
        print("=" * 60)
        
        return result


class OLLAMA_PT_panel(Panel):
    """Ollama AI Assistant Panel"""
    bl_label = "Qwen2.5-Coder Assistant"
    bl_idname = "OLLAMA_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ollama'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Model selection
        box = layout.box()
        box.label(text="AI Model:", icon='NETWORK_DRIVE')
        box.prop(scene, "ollama_model", text="")
        
        # Test connection button
        box.operator("ollama.test_connection", icon='PLUGIN', text="Test Connection")

        # Advanced settings
        row = box.row()
        row.prop(scene, "ollama_max_tokens", text="Max Tokens")

        layout.separator()

        # Command input
        box = layout.box()
        box.label(text="Command:", icon='CONSOLE')
        box.prop(scene, "ollama_prompt", text="")
        
        # Options
        row = box.row()
        row.prop(scene, "ollama_auto_material", text="Auto Material")
        row.prop(scene, "ollama_debug_mode", text="Debug", toggle=True)

        # Execute button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("ollama.execute", icon='PLAY', text="Generate & Execute")

        # Show last code
        if hasattr(scene, "ollama_last_code") and scene.ollama_last_code:
            layout.separator()
            box = layout.box()
            box.label(text="Generated Code:", icon='TEXT')
            
            col = box.column(align=True)
            code_lines = scene.ollama_last_code.split('\n')[:20]
            for line in code_lines:
                col.label(text=line[:70])
            
            if len(scene.ollama_last_code.split('\n')) > 20:
                col.label(text="... (truncated, check console)")

        # Examples
        layout.separator()
        help_box = layout.box()
        help_box.label(text="Example Prompts:", icon='QUESTION')
        
        col = help_box.column(align=True)
        col.label(text="✅ Simple examples:")
        col.label(text="• 'red cube'")
        col.label(text="• '5 blue spheres in a line'")
        col.label(text="• 'circle of 8 cubes'")
        col.label(text="• 'pyramid of cylinders'")
        
        col.separator()
        col.label(text="⚡ Tip: Keep prompts simple!")
        col.label(text="Model: Qwen2.5-Coder:3b")


def register():
    bpy.utils.register_class(OLLAMA_OT_test_connection)
    bpy.utils.register_class(OLLAMA_OT_execute)
    bpy.utils.register_class(OLLAMA_PT_panel)

    bpy.types.Scene.ollama_prompt = StringProperty(
        name="Prompt",
        description="Natural language command for Blender",
        default=""
    )

    bpy.types.Scene.ollama_model = EnumProperty(
        name="Model",
        description="Ollama model to use",
        items=[
            ('qwen2.5-coder:3b', "Qwen2.5-Coder 3B", "Fast, efficient code generation"),
            ('qwen2.5-coder:7b', "Qwen2.5-Coder 7B", "More capable, slower"),
            ('qwen2.5-coder:latest', "Qwen2.5-Coder Latest", "Latest version"),
            ('codellama:7b', "CodeLlama 7B", "Alternative model"),
            ('deepseek-coder:6.7b', "DeepSeek Coder 6.7B", "Alternative model"),
        ],
        default='qwen2.5-coder:3b'
    )

    bpy.types.Scene.ollama_max_tokens = IntProperty(
        name="Max Tokens",
        description="Maximum tokens for code generation",
        default=600,
        min=200,
        max=1500
    )

    bpy.types.Scene.ollama_auto_material = BoolProperty(
        name="Auto Material",
        description="Automatically add colored materials to objects",
        default=True
    )

    bpy.types.Scene.ollama_debug_mode = BoolProperty(
        name="Debug Mode",
        description="Print detailed debug info to console",
        default=False
    )

    bpy.types.Scene.ollama_last_code = StringProperty(default="")


def unregister():
    bpy.utils.unregister_class(OLLAMA_OT_execute)
    bpy.utils.unregister_class(OLLAMA_OT_test_connection)
    bpy.utils.unregister_class(OLLAMA_PT_panel)

    del bpy.types.Scene.ollama_prompt
    del bpy.types.Scene.ollama_model
    del bpy.types.Scene.ollama_max_tokens
    del bpy.types.Scene.ollama_auto_material
    del bpy.types.Scene.ollama_debug_mode
    del bpy.types.Scene.ollama_last_code


if __name__ == "__main__":
    register()