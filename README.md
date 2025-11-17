# Ollama AI Assistant for Blender (Qwen2.5-Coder)

A Blender addon that lets you control Blender using natural language commands powered by Qwen2.5-Coder via Ollama.

## Features

- 🎨 **Natural Language Control**: Create 3D scenes using simple text commands
- 🚀 **Local AI**: Runs completely offline using Ollama
- 🔧 **Smart Code Generation**: Optimized prompts for Qwen2.5-Coder models
- 🎯 **Auto-fixing**: Automatically corrects common Blender API issues
- 🌈 **Material Support**: Auto-generates colored materials for objects
- 🐛 **Debug Mode**: Detailed logging for troubleshooting

## Requirements

- **Blender**: 3.0 or higher
- **Ollama**: Latest version ([download here](https://ollama.ai))
- **Python requests module**: Install via pip
- **Qwen2.5-Coder model**: 3B recommended for speed

## Installation

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai](https://ollama.ai)

### 2. Pull Qwen2.5-Coder Model

Open terminal/command prompt and run:

```bash
ollama pull qwen2.5-coder:3b
```

For better quality (but slower), use the 7B model:

```bash
ollama pull qwen2.5-coder:7b
```

### 3. Start Ollama Server

```bash
ollama serve
```

Keep this running in the background while using the addon.

### 4. Install Python Requests Module

Open Blender's Python console and run:

```python
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
```

Or install it in your system Python if Blender uses that.

### 5. Install the Addon

1. Download the `ollama_assistant.py` file
2. In Blender, go to **Edit → Preferences → Add-ons**
3. Click **Install...** and select the downloaded file
4. Enable the addon by checking the box next to "Ollama AI Assistant"

## Usage

### Basic Workflow

1. Open Blender's **Sidebar** (press `N` in 3D View)
2. Click the **Ollama** tab
3. Click **Test Connection** to verify Ollama is running
4. Enter a command in the text field
5. Click **Generate & Execute**

### Example Commands

#### Simple Objects
```
red cube
blue sphere at (2, 0, 0)
5 green cylinders in a row
```

#### Patterns
```
circle of 8 cubes
pyramid of spheres with 4 levels
grid of 3x3 cylinders
```

#### Materials
```
rainbow colored spheres in a line
cube with metallic red material
shiny gold sphere
```

#### Complex Scenes
```
solar system with sun and 3 planets
simple house with roof
forest of 10 trees
```

### Tips for Best Results

- ✅ **Keep it simple**: Short, clear commands work best
- ✅ **Be specific**: Include colors, positions, or quantities
- ✅ **Use basic shapes**: Cube, sphere, cylinder, cone, torus
- ❌ **Avoid**: Very complex requests, animations, physics simulations
- 💡 **Start small**: Test simple commands before complex scenes

## Settings

### Model Selection

- **Qwen2.5-Coder 3B** (Default): Fast, efficient, good for simple tasks
- **Qwen2.5-Coder 7B**: More capable, handles complex requests better
- **Other models**: CodeLlama, DeepSeek-Coder also supported

### Max Tokens

Controls how much code the AI generates:
- **300-500**: Simple objects
- **600-800**: Medium complexity
- **1000-1500**: Complex scenes

### Debug Mode

Enable to see detailed information in Blender's console:
- Raw generated code
- API fixes applied
- Execution logs
- Error traces

### Auto Material

When enabled, automatically creates colored materials for generated objects.

## Troubleshooting

### "requests module not available"

Install the requests library:
```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
```

### "Cannot connect to Ollama"

1. Make sure Ollama is installed
2. Start the server: `ollama serve`
3. Verify it's running: visit `http://localhost:11434` in browser

### "No valid code generated"

1. Check Debug Mode to see raw output
2. Try a simpler prompt
3. Increase Max Tokens setting
4. Try the 7B model for better quality

### "Syntax Error" or "Execution Error"

1. Enable Debug Mode to see the problematic code
2. Check console for detailed error messages
3. Try rephrasing your prompt
4. Report persistent issues with example prompts

### Model Not Found

Pull the model first:
```bash
ollama pull qwen2.5-coder:3b
```

Verify available models:
```bash
ollama list
```

## Technical Details

### How It Works

1. **Prompt Engineering**: Your natural language command is wrapped in a specialized prompt optimized for Qwen2.5-Coder
2. **Code Generation**: Ollama streams Python code from the AI model
3. **API Fixes**: Common Blender API mistakes are automatically corrected
4. **Syntax Validation**: Code is parsed to catch syntax errors before execution
5. **Safe Execution**: Code runs in a controlled environment with proper error handling

### Automatic Fixes

The addon automatically corrects:
- Old Blender API calls (2.7x → 3.x)
- Missing object linking to scene
- Parent/child relationship errors
- Material color format issues (RGB → RGBA)
- Invalid enum values
- Unclosed brackets/parentheses
- Duplicate imports

### Complexity Detection

The addon analyzes your prompt and adjusts:
- Token limits (simple: 300, complex: 800)
- Generation parameters
- System prompt detail level

## Performance Tips

### For Faster Generation
- Use the 3B model
- Lower Max Tokens setting
- Use simpler prompts
- Close other applications

### For Better Quality
- Use the 7B model
- Increase Max Tokens
- Be more specific in prompts
- Enable Debug Mode to refine

## Limitations

- Cannot modify existing objects (always creates new scene)
- No animation or physics support
- Limited understanding of very complex spatial relationships
- Occasional API hallucinations (mostly auto-fixed)
- Requires good GPU/CPU for larger models

## Advanced Usage

### Using Custom System Prompts

Edit the `generate_code()` method to customize the AI's behavior:

```python
system_msg = """Your custom instructions here..."""
```

### Extending API Fixes

Add custom fixes in the `fix_blender_api()` method:

```python
# Your custom regex patterns
code = re.sub(r'your_pattern', r'replacement', code)
```

### Logging

All operations are logged to Blender's console. Enable Debug Mode for verbose output.

## Contributing

Found a bug or have a feature request? Common issues include:
- API compatibility problems with new Blender versions
- Model-specific quirks
- Prompt engineering improvements

## Credits

- **Blender**: Open source 3D creation suite
- **Ollama**: Local AI model runner
- **Qwen2.5-Coder**: Code generation model by Alibaba Cloud
- **Addon Author**: Community Contributor

## License

This addon is provided as-is for educational and creative purposes.

## Version History

- **1.3.2**: Current version with improved error handling
- Enhanced material fixes
- Better code extraction
- Duplicate link prevention

## Support

For issues:
1. Enable Debug Mode
2. Check Blender console output
3. Verify Ollama connection with Test Connection button
4. Try simpler prompts first

## Acknowledgments

Thanks to the Blender and Ollama communities for making local AI-assisted 3D creation possible!
