import agent_framework
import importlib.metadata as md

print("=== agent_framework version ===")
try:
    print(md.version("agent-framework"))
except Exception as e:
    print(f"core package not found: {e}")

try:
    print("agent-framework-azure-ai:", md.version("agent-framework-azure-ai"))
except Exception as e:
    print(f"azure-ai package not found: {e}")

print("\n=== Public names in agent_framework ===")
for name in sorted(dir(agent_framework)):
    if not name.startswith("_"):
        print(name)

print("\n=== Public names in agent_framework.azure ===")
try:
    import agent_framework.azure as af_azure
    for name in sorted(dir(af_azure)):
        if not name.startswith("_"):
            print(name)
except Exception as e:
    print(f"Could not import agent_framework.azure: {e}")
