// Local smoke test only: execute real upstream RTL and observe a store of 42.
// This does not replace upstream riscv-tests or ISA compliance testing.
module tb_silicon;
  reg clk=0;
  always #5 clk=~clk;
  reg resetn=0;
  wire trap, valid, instruction;
  wire [31:0] address, wdata;
  wire [3:0] wstrb;
  reg [31:0] rdata;
  reg [31:0] memory [0:255];
  integer i, cycles=0;
  initial begin
    for(i=0;i<256;i=i+1) memory[i]=0;
    memory[0]=32'h02a00093; // addi x1,x0,42
    memory[1]=32'h10000113; // addi x2,x0,256
    memory[2]=32'h00112023; // sw x1,0(x2)
    memory[3]=32'h0000006f; // jal x0,0 (loop after observable store)
    repeat(5) @(posedge clk);
    @(negedge clk) resetn=1;
  end
  always @* rdata=address<1024 ? memory[address>>2] : 32'h0;
  always @(posedge clk) begin
    if(resetn) begin
      cycles=cycles+1;
      if(trap) $fatal(1,"RTL trapped before test completion");
      if(valid && |wstrb) begin
        if(address==256 && wstrb==4'b1111 && wdata==42) begin
          $display("SILICON_RTL_PASS cycles=%0d store=%0d",cycles,wdata);
          $finish;
        end
        $fatal(1,"Unexpected RTL write address=%h data=%h",address,wdata);
      end
      if(cycles>2000) $fatal(1,"RTL test timed out");
    end
  end
  picorv32 #(.ENABLE_COUNTERS(0), .ENABLE_IRQ(0), .COMPRESSED_ISA(0),
             .ENABLE_MUL(0), .ENABLE_DIV(0)) cpu (
    .clk(clk), .resetn(resetn), .trap(trap),
    .mem_valid(valid), .mem_instr(instruction), .mem_ready(1'b1),
    .mem_addr(address), .mem_wdata(wdata), .mem_wstrb(wstrb), .mem_rdata(rdata),
    .irq(32'b0), .pcpi_wr(1'b0), .pcpi_rd(32'b0), .pcpi_wait(1'b0), .pcpi_ready(1'b0)
  );
endmodule
