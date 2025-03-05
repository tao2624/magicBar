#include "protocol.h"
#include "stm32f10x.h"  
#include <stdio.h>

//��У���
static uint8_t Get_Check(uint8_t *data, uint16_t len) {
	uint8_t sum = 0;
	uint16_t i;
	for (i = 0; i < len; i++) {
		sum += data[i];
	}
	return sum;
}

//��������ѧϰָ�����
uint16_t IR_Learn_Pack(uint8_t *data, uint8_t index) {
	uint8_t *p = data;
	*p++ = FRAME_START;
	*p++ = 0x08;
	*p++ = 0x00;
	*p++ = MODULE_ADDR;
	*p++ = 0x10;
	*p++ = index;
	*p = Get_Check(&data[3], p - data - 3);
	p++;
	*p++ = FRAME_END;
	return p - data;
}

//�������뷢��ָ�����
uint16_t IR_Send_Pack(uint8_t *data, uint8_t index) {
	uint8_t *p = data;
	*p++ = FRAME_START;
	*p++ = 0x08;
	*p++ = 0x00;
	*p++ = MODULE_ADDR;
	*p++ = 0x12;
	*p++ = index;
	*p = Get_Check(&data[3], p - data - 3);
	p++;
	*p++ = FRAME_END;
	return p - data;
}
