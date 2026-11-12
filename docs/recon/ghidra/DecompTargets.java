// Decompila apenas os enderecos passados como argumentos (offsets relativos à imagem).
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
public class DecompTargets extends GhidraScript {
  public void run() throws Exception {
    DecompInterface d = new DecompInterface(); d.openProgram(currentProgram);
    for (String a : getScriptArgs()) {
      Address addr = currentProgram.getImageBase().add(Long.decode(a));
      new DisassembleCommand(addr, null, true).applyTo(currentProgram, monitor);
      Function f = getFunctionAt(addr);
      if (f == null) { new CreateFunctionCmd(addr).applyTo(currentProgram, monitor); f = getFunctionAt(addr); }
      println("===== " + a + " " + (f == null ? "NOFUNC" : f.getName()));
      if (f == null) continue;
      DecompileResults r = d.decompileFunction(f, 120, monitor);
      println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : ("FAIL " + r.getErrorMessage()));
    }
  }
}
