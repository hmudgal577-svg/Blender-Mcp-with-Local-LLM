# 🤖 DeepSeek Robotics Assistant - Blender Addon

![DeepSeek Robotics](https://img.shields.io/badge/Blender-3.0%2B-orange)
![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

An AI-powered Blender addon that generates 3D robotic models and mechanical structures using natural language commands. Powered by DeepSeek AI models via Ollama, with intelligent fallback code for guaranteed results.

![DeepSeek Robotics Interface](screenshot.png)
*Creating a robot arm with 6 joints and gripper using natural language*

---

## ✨ Features

### 🎯 Core Capabilities
- **AI-Powered Generation**: Create complex 3D models using natural language descriptions
- **Intelligent Fallbacks**: Guaranteed working code for common objects (robots, furniture, vehicles)
- **Multiple AI Models**: Support for DeepSeek R1 (7B, 14B, Latest) and DeepSeek Coder
- **Auto Materials**: Automatic material assignment with metallic/realistic colors
- **Real-time Debugging**: View generated code and execution logs
- **Syntax Validation**: Pre-execution code validation to prevent errors

### 🛠️ Supported Objects
- **Robotics**: Articulated arms, grippers, joints, manipulators
- **Furniture**: Tables, chairs, desks, stools
- **Primitives**: Cubes, spheres, cylinders (with count support)
- **Structures**: Houses, buildings, trees
- **Vehicles**: Cars, simple automobiles
- **Custom**: Any description - AI will attempt to generate

---

## 📋 Requirements

### Software
- **Blender**: 3.0 or higher
- **Python**: 3.7+ (included with Blender)
- **Ollama**: Latest version

### Python Packages
```bash
pip install requests
```

### AI Models (via Ollama)
```bash
# Fast (Recommended for testing)
ollama pull deepseek-r1:7b

# Balanced
ollama pull deepseek-r1:14b

# Best Quality
ollama pull deepseek-r1:latest

# Code-Focused
ollama pull deepseek-coder:6.7b
```

---

## 🚀 Installation

### Step 1: Install Ollama
1. Download from [ollama.ai](https://ollama.ai)
2. Install and start the service:
   ```bash
   ollama serve
   ```

### Step 2: Install Python Dependencies
```bash
# Windows
python -m pip install requests

# macOS/Linux
pip3 install requests

# Or install in Blender's Python
/path/to/blender/python/bin/python -m pip install requests
```

### Step 3: Install Addon
1. Download `deepseek_robotics_assistant.py`
2. Open Blender → Edit → Preferences → Add-ons
3. Click "Install..." and select the `.py` file
4. Enable "DeepSeek Robotics Assistant - FIXED"
5. Find the panel in 3D View → Sidebar → DeepSeek tab

---

## 📖 Usage Guide

### Basic Workflow

1. **Start Ollama** (must be running)
   ```bash
   ollama serve
   ```

2. **Open Blender** and locate the DeepSeek panel (N key → DeepSeek tab)

3. **Select Model** (default: DeepSeek R1 7B)

4. **Test Connection** - Click "Test Connection" to verify Ollama

5. **Enter Command** - Type natural language description:
   ```
   robot arm with 6 joints and gripper
   create a simple table with 4 legs
   make a mechanical joint assembly
   ```

6. **Choose Mode**:
   - ✅ **Fallback Mode** (Guaranteed): Uses pre-built templates
   - 🤖 **AI Mode**: Generates custom code via AI

7. **Create** - Click the button and wait for generation

### Example Commands

#### Robotics
```
robot arm with gripper
articulated manipulator with 5 joints
robotic hand with fingers
mechanical arm assembly
```

#### Furniture
```
simple table with 4 legs
wooden chair with backrest
desk with drawers
```

#### Primitives
```
5 cubes in a row
10 spheres arranged in circle
3 cylinders stacked vertically
```

#### Complex Objects
```
simple house with roof and door
tree with trunk and leaves
basic car with 4 wheels
```

---

## ⚙️ Interface Overview

### Model Selection
| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| DeepSeek R1 7B | ⚡ Fast | ⭐⭐⭐ | Testing, simple objects |
| DeepSeek R1 14B | 🔥 Medium | ⭐⭐⭐⭐ | Balanced performance |
| DeepSeek R1 Latest | 🐌 Slow | ⭐⭐⭐⭐⭐ | Complex models |
| DeepSeek Coder | ⚡ Fast | ⭐⭐⭐⭐ | Code-heavy tasks |

### Options
- **Use Fallback**: Skip AI, use guaranteed template code
- **Materials**: Auto-apply metallic materials to generated objects
- **Debug**: Show generated code in console and panel

### Status Display
- **Last**: Execution time of previous generation
- **Code**: Preview of generated Python code (first 6 lines)

---

## 🎬 Demo Video

[Watch the demo video](demo.mp4) showing:
- Installing and setting up the addon
- Testing Ollama connection
- Creating a robot arm in real-time
- Switching between AI and fallback modes
- Material application

---

## 🔧 Troubleshooting

### "requests not installed"
```bash
pip install requests
# Or in Blender's Python
/path/to/blender/python/bin/python -m pip install requests
```

### "❌ Start Ollama: ollama serve"
- Ollama is not running
- Open terminal and run: `ollama serve`
- Keep the terminal open while using the addon

### "Model not found"
```bash
# Pull the model first
ollama pull deepseek-r1:7b
```

### AI generates broken code
- Enable "Use Fallback" mode for guaranteed results
- Try DeepSeek Coder model for better code quality
- Check Debug mode to see what code was generated

### Objects not appearing
- Check Blender console (Window → Toggle System Console)
- Look for Python execution errors
- Ensure generated code has `bpy.context.collection` links

---

## 🏗️ Architecture

### Code Flow
```
User Input → AI/Fallback → Code Generation → Syntax Check → Execute → Materials
```

### Key Components

#### 1. Connection Manager
- Tests Ollama availability
- Validates model access
- Lists available models

#### 2. Code Generator
- **AI Path**: Streams response from Ollama API
- **Fallback Path**: Uses keyword-based template selection
- Extracts clean Python code from responses

#### 3. Execution Engine
- Validates syntax with AST parser
- Executes in sandboxed environment
- Provides mathutils (Vector, Matrix, Euler)

#### 4. Material System
- 6 pre-defined PBR materials
- Automatic assignment to mesh objects
- Metallic workflow (0.7 metallic, 0.3 roughness)

---

## 🎨 Generated Code Structure

All generated code follows this pattern:

```python
import bpy
from mathutils import Vector

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Create geometry
bpy.ops.mesh.primitive_cube_add(...)
obj = bpy.context.active_object
obj.name = "MyObject"

# Link to collection
bpy.context.collection.objects.link(obj)
```

---

## 📊 Performance Benchmarks

| Operation | Time (Fallback) | Time (AI 7B) | Time (AI 14B) |
|-----------|----------------|--------------|---------------|
| Robot Arm | 0.01s | 3-8s | 8-15s |
| Simple Table | 0.01s | 2-5s | 5-10s |
| Custom Object | N/A | 5-20s | 10-30s |

*Tested on M1 Mac / RTX 3080*

---

## 🛡️ Safety Features

- **Syntax Validation**: All code checked before execution
- **Sandboxed Execution**: Limited scope prevents system access
- **Error Handling**: Graceful failures with user feedback
- **Code Preview**: See what will execute before running
- **Fallback Mode**: Guaranteed safe code templates

---

## 🔮 Future Enhancements

- [ ] Animation generation
- [ ] Material customization UI
- [ ] Rigging automation
- [ ] Physics setup
- [ ] Export presets
- [ ] Cloud AI model support
- [ ] Batch generation
- [ ] Template library manager

---

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional fallback templates
- Better code extraction algorithms
- UI/UX improvements
- Documentation
- Testing

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **DeepSeek AI** - AI models
- **Ollama** - Local AI inference
- **Blender Foundation** - 3D software
- **Community** - Feedback and testing

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/repo/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/repo/wiki)

---

## 📝 Changelog

### v3.2.0 (Current)
- ✅ Fixed all major bugs
- ✅ Added intelligent fallback system
- ✅ Improved code extraction
- ✅ Better error handling
- ✅ Material auto-assignment
- ✅ Debug mode with code preview

### v3.1.0
- Added DeepSeek Coder support
- Syntax validation
- Connection testing

### v3.0.0
- Initial AI-powered version
- Ollama integration
- Basic fallback templates

---

**Made with ❤️ for the Blender community**
