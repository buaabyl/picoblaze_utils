`timescale 1 ps / 1ps

module pblaze 
(
    input   clk,
    input   rst,
    input   rx,
    output  tx
);

wire [9:0]  address;
wire [17:0] instruction;
wire [7:0]  port_id;
wire [7:0]  out_port;
reg [7:0]   in_port;
wire        write_strobe;
wire        read_strobe;


reg [4:0]   baud_count;
reg         en_16_x_baud;
wire        write_to_uart;
wire        tx_full;
wire        tx_half_full;
reg         read_from_uart;
wire [7:0]  rx_data;
wire        rx_data_present;
wire        rx_full;
wire        rx_half_full;


kcpsm3 processor (
    .address(address),
    .instruction(instruction),
    .port_id(port_id),
    .write_strobe(write_strobe),
    .out_port(out_port),
    .read_strobe(read_strobe),
    .in_port(in_port),
    .interrupt(),
    .interrupt_ack(),
    .reset(1'b0),
    .clk(clk)
);

kcpsm3_rom program_rom
(
    .clk(clk),
    .address(address),
    .instruction(instruction)
);

uart_tx transmit (
    .data_in(out_port),
    .write_buffer(write_to_uart),
    .reset_buffer(1'b0),
    .en_16_x_baud(en_16_x_baud),
    .serial_out(tx),
    .buffer_full(tx_full),
    .buffer_half_full(tx_half_full),
    .clk(clk)
);

uart_rx receive (
    .serial_in(rx),
    .data_out(rx_data),
    .read_buffer(read_from_uart),
    .reset_buffer(1'b0),
    .en_16_x_baud(en_16_x_baud),
    .buffer_data_present(rx_data_present),
    .buffer_full(rx_full),
    .buffer_half_full(rx_half_full),
    .clk(clk)
);

always @(posedge clk)
begin
    case(port_id)
    8'h00: 
    begin
        in_port <= {3'b 000,rx_data_present,rx_full,rx_half_full,tx_full,tx_half_full};
    end
    8'h01: 
    begin
        in_port <= rx_data;
    end
    default : 
    begin
        in_port <= 8'b0;
    end
    endcase
end


always @(posedge clk)
begin
    // Form read strobe for UART receiver FIFO buffer.
    // The fact that the read strobe will occur after the actual data is read by 
    // the KCPSM3 is acceptable because it is really means 'I have read you'!
    read_from_uart <= read_strobe && (port_id == 8'h01);
end

assign write_to_uart = write_strobe & (port_id == 8'h01);


//48M / (115200 * 16)
//  = 26
always @(posedge clk)
begin
    if (baud_count == 25) begin
        baud_count <= 1'b0;
        en_16_x_baud <= 1'b1;
    end
    else begin
        baud_count <= baud_count + 1;
        en_16_x_baud <= 1'b0;
    end
end


endmodule

