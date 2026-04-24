import logging
import socket
import struct
import threading
import time


class ModbusTcpError(Exception):
    """Modbus TCP 通信异常。"""


class ModbusTcpClient:
    """最小可控的 Modbus TCP 客户端。
    
    提供对 Modbus TCP 协议的底层支持，包括：
    - 单个线圈写入（功能码 0x05）
    - 离散输入读取（功能码 0x02）
    - 输入寄存器读取（功能码 0x04）
    
    支持配置连接超时和响应超时参数。
    """

    # Modbus 异常响应中的异常码描述映射
    _EXCEPTION_MESSAGES = {
        0x01: "非法功能",
        0x02: "非法数据地址",
        0x03: "非法数据值",
        0x04: "从站设备故障",
        0x05: "确认",
        0x06: "从站设备忙",
        0x08: "存储奇偶校验错误",
        0x0A: "网关路径不可用",
        0x0B: "网关目标设备响应失败",
    }

    def __init__(self):
        """初始化客户端，重置事务 ID 和线程锁。"""
        self.logger = logging.getLogger("ModbusTcpClient")
        self._transaction_id = 0
        self._transaction_lock = threading.Lock()

    def write_single_coil(
        self,
        host,
        port,
        unit_id,
        offset,
        value,
        *,
        connect_timeout_ms=1500,
        response_timeout_ms=1500,
    ):
        """写入单个线圈（功能码 0x05）。
        
        参数:
            host: 目标设备 IP 地址
            port: 目标设备端口号（默认 502）
            unit_id: 从站单元 ID
            offset: 线圈地址偏移量
            value: 线圈值（True/False 或 1/0）
            connect_timeout_ms: 连接超时时间（毫秒）
            response_timeout_ms: 响应超时时间（毫秒）
        """
        # 将布尔值转换为 Modbus 协议要求的格式：0xFF00 表示 ON，0x0000 表示 OFF
        coil_value = 0xFF00 if bool(value) else 0x0000
        request_pdu = struct.pack(">BHH", 0x05, int(offset), coil_value)
        response_pdu = self._send_request(
            host,
            port,
            unit_id,
            request_pdu,
            connect_timeout_ms=connect_timeout_ms,
            response_timeout_ms=response_timeout_ms,
        )

        # 验证响应是否与请求一致
        if response_pdu != request_pdu:
            raise ModbusTcpError("PLC 写单个线圈失败: 返回报文与请求不一致")

        self.logger.info(
            "[MODBUS_WRITE_SINGLE_COIL] host=%s port=%s unit_id=%s offset=%s value=%s result=ok",
            host,
            port,
            unit_id,
            offset,
            bool(value),
        )

    def read_discrete_inputs(
        self,
        host,
        port,
        unit_id,
        offset,
        count,
        *,
        connect_timeout_ms=1500,
        response_timeout_ms=1500,
    ):
        """读取离散输入状态（功能码 0x02）。
        
        参数:
            host: 目标设备 IP 地址
            port: 目标设备端口号（默认 502）
            unit_id: 从站单元 ID
            offset: 起始地址偏移量
            count: 要读取的离散输入数量
            connect_timeout_ms: 连接超时时间（毫秒）
            response_timeout_ms: 响应超时时间（毫秒）
        
        返回:
            离散输入状态的布尔值列表
        """
        request_pdu = struct.pack(">BHH", 0x02, int(offset), int(count))
        response_pdu = self._send_request(
            host,
            port,
            unit_id,
            request_pdu,
            connect_timeout_ms=connect_timeout_ms,
            response_timeout_ms=response_timeout_ms,
        )

        if len(response_pdu) < 2:
            raise ModbusTcpError("PLC 读离散输入失败: 返回报文长度不足")

        byte_count = response_pdu[1]
        data = response_pdu[2:]
        if len(data) != byte_count:
            raise ModbusTcpError("PLC 读离散输入失败: 数据长度不匹配")

        # 将字节数据逐位解析为布尔值
        values = []
        for byte in data:
            for bit_index in range(8):
                values.append(bool((byte >> bit_index) & 0x01))
                if len(values) >= count:
                    return values
        return values

    def read_input_registers(
        self,
        host,
        port,
        unit_id,
        offset,
        count,
        *,
        connect_timeout_ms=1500,
        response_timeout_ms=1500,
    ):
        """读取输入寄存器（功能码 0x04）。
        
        参数:
            host: 目标设备 IP 地址
            port: 目标设备端口号（默认 502）
            unit_id: 从站单元 ID
            offset: 起始地址偏移量
            count: 要读取的寄存器数量
            connect_timeout_ms: 连接超时时间（毫秒）
            response_timeout_ms: 响应超时时间（毫秒）
        
        返回:
            寄存器读取到的无符号整数列表
        """
        request_pdu = struct.pack(">BHH", 0x04, int(offset), int(count))
        response_pdu = self._send_request(
            host,
            port,
            unit_id,
            request_pdu,
            connect_timeout_ms=connect_timeout_ms,
            response_timeout_ms=response_timeout_ms,
        )

        if len(response_pdu) < 2:
            raise ModbusTcpError("PLC 读输入寄存器失败: 返回报文长度不足")

        byte_count = response_pdu[1]
        data = response_pdu[2:]
        expected_bytes = int(count) * 2
        if byte_count != expected_bytes or len(data) != expected_bytes:
            raise ModbusTcpError("PLC 读输入寄存器失败: 数据长度不匹配")

        # 将字节数据解析为无符号整数列表
        return list(struct.unpack(f">{count}H", data))

    def _next_transaction_id(self):
        """生成下一个事务 ID，范围 1-65535，避免使用 0。
        
        返回:
            当前事务 ID（原子递增）
        """
        with self._transaction_lock:
            self._transaction_id = (self._transaction_id + 1) & 0xFFFF
            if self._transaction_id == 0:
                self._transaction_id = 1
            return self._transaction_id

    def _send_request(
        self,
        host,
        port,
        unit_id,
        pdu,
        *,
        connect_timeout_ms,
        response_timeout_ms,
    ):
        """发送 Modbus TCP 请求并接收响应。
        
        完整流程：
        1. 构建 MBAP 请求头（事务 ID + 协议 ID + 长度 + Unit ID）
        2. 建立 TCP 连接并发送请求
        3. 接收并验证响应头
        4. 接收 PDU 数据部分
        5. 检查异常响应
        
        参数:
            host: 目标设备 IP 地址
            port: 目标设备端口号
            unit_id: 从站单元 ID
            pdu: Modbus 协议数据单元（功能码 + 数据）
            connect_timeout_ms: 连接超时时间（毫秒）
            response_timeout_ms: 响应超时时间（毫秒）
        
        返回:
            响应 PDU 数据（不含 MBAP 头）
        
        异常:
            ModbusTcpError: 通信失败、校验错误或超时
        """
        # 获取递增的事务 ID
        transaction_id = self._next_transaction_id()
        protocol_id = 0
        unit_id = int(unit_id)
        port = int(port)
        connect_timeout_s = max(float(connect_timeout_ms) / 1000.0, 0.1)
        response_timeout_s = max(float(response_timeout_ms) / 1000.0, 0.1)
        
        # 构建 MBAP 请求头：事务 ID(2) + 协议 ID(2) + 长度(2) + Unit ID(1)
        length = len(pdu) + 1
        request_adu = struct.pack(">HHHB", transaction_id, protocol_id, length, unit_id) + pdu
        start = time.perf_counter()

        self.logger.info(
            "[MODBUS_REQUEST] host=%s port=%s unit_id=%s function=%s transaction_id=%s connect_timeout_ms=%s response_timeout_ms=%s",
            host,
            port,
            unit_id,
            pdu[0],
            transaction_id,
            connect_timeout_ms,
            response_timeout_ms,
        )

        try:
            with socket.create_connection((host, port), timeout=connect_timeout_s) as sock:
                sock.settimeout(response_timeout_s)
                sock.sendall(request_adu)

                # 接收 7 字节的 MBAP 响应头
                response_header = self._recv_exact(sock, 7)
                resp_tid, resp_protocol_id, resp_length, resp_unit_id = struct.unpack(">HHHB", response_header)

                # 验证响应头各字段
                if resp_tid != transaction_id:
                    raise ModbusTcpError("PLC 返回事务标识不匹配")
                if resp_protocol_id != protocol_id:
                    raise ModbusTcpError("PLC 返回协议标识不匹配")
                if resp_unit_id != unit_id:
                    raise ModbusTcpError("PLC 返回 Unit ID 不匹配")
                if resp_length < 2:
                    raise ModbusTcpError("PLC 返回长度非法")

                # 接收 PDU 数据部分
                response_pdu = self._recv_exact(sock, resp_length - 1)
                if not response_pdu:
                    raise ModbusTcpError("PLC 返回空响应")

                response_function_code = response_pdu[0]
                request_function_code = pdu[0]
                
                # 检查是否为异常响应（功能码最高位为 1）
                if response_function_code == (request_function_code | 0x80):
                    exception_code = response_pdu[1] if len(response_pdu) > 1 else None
                    raise ModbusTcpError(self._format_exception_message(exception_code))
                
                # 验证功能码是否匹配
                if response_function_code != request_function_code:
                    raise ModbusTcpError("PLC 返回功能码不匹配")

                elapsed_ms = (time.perf_counter() - start) * 1000
                self.logger.info(
                    "[MODBUS_RESPONSE] host=%s port=%s unit_id=%s function=%s transaction_id=%s elapsed_ms=%.2f result=ok",
                    host,
                    port,
                    unit_id,
                    response_function_code,
                    transaction_id,
                    elapsed_ms,
                )
                return response_pdu
        except socket.timeout as exc:
            raise ModbusTcpError("PLC 通信超时") from exc
        except OSError as exc:
            raise ModbusTcpError(f"PLC 连接失败: {exc}") from exc

    def _recv_exact(self, sock, size):
        """从 socket 精确接收指定字节数的数据。
        
        参数:
            sock: socket 连接对象
            size: 要接收的字节数
        
        返回:
            指定长度的字节数据
        
        异常:
            ModbusTcpError: 连接断开或接收失败
        """
        chunks = bytearray()
        while len(chunks) < size:
            chunk = sock.recv(size - len(chunks))
            if not chunk:
                raise ModbusTcpError("PLC 连接已断开")
            chunks.extend(chunk)
        return bytes(chunks)

    def _format_exception_message(self, exception_code):
        """将 Modbus 异常码格式化为可读的中文错误信息。
        
        参数:
            exception_code: 异常码（0x01-0x0B），None 表示未知异常
        
        返回:
            格式化的中文错误描述字符串
        """
        if exception_code is None:
            return "PLC 返回 Modbus 异常响应"
        description = self._EXCEPTION_MESSAGES.get(exception_code, "未知异常")
        return f"PLC 写单个线圈失败: 异常码 {exception_code:02X} ({description})"
