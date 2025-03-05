#include "CyberryPotter.h"

extern struct IMU_t IMU;
extern struct LED_t LED;
Cyberry_Potter_t Cyberry_Potter;
Module_t Module;

void Module_None_Mode0_Handler(void)
{
	LED.Operate(BLINK_10HZ);
}

void Module_None_Mode1_Handler(void)
{
	LED.Operate(BLINK_5HZ);
}

/// @brief initialize reqired peripheral and function according to module type
/// @param  None
void Module_Init(void)
{
	switch (Module.Type) {
		case Module_Type_None:
			Module.Mode0_Handler = &Module_None_Mode0_Handler;
			Module.Mode1_Handler = &Module_None_Mode1_Handler;
			break;
		case Module_Type_0:
			Module0_Init();
			printf("Module Module_Type_0 Init\n");
			Module.Mode0_Handler = &Module0_Mode0_Handler;
			Module.Mode1_Handler = &Module0_Mode1_Handler;
			break;
		case Module_Type_1:
			Module1_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module1_Mode0_Handler;
			Module.Mode1_Handler = &Module1_Mode1_Handler;
			break;
		case Module_Type_2:
			Module2_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module2_Mode0_Handler;
			Module.Mode1_Handler = &Module2_Mode1_Handler;
			break;
		case Module_Type_3:
			Module3_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module3_Mode0_Handler;
			Module.Mode1_Handler = &Module3_Mode1_Handler;
			break;
		case Module_Type_4:
			Module4_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module4_Mode0_Handler;
			Module.Mode1_Handler = &Module4_Mode1_Handler;
			break;
		case Module_Type_5:
			Module5_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module5_Mode0_Handler;
			Module.Mode1_Handler = &Module5_Mode1_Handler;
			break;
		case Module_Type_6:
			Module6_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module6_Mode0_Handler;
			Module.Mode1_Handler = &Module6_Mode1_Handler;
			break;
		case Module_Type_7:
			Module7_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module7_Mode0_Handler;
			Module.Mode1_Handler = &Module7_Mode1_Handler;
			break;
		case Module_Type_8:
			Module8_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module8_Mode0_Handler;
			Module.Mode1_Handler = &Module8_Mode1_Handler;
			break;
		case Module_Type_9:
			Module9_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module9_Mode0_Handler;
			Module.Mode1_Handler = &Module9_Mode1_Handler;
			break;
		case Module_Type_10: 
			Module10_Init();
			printf("Module %d Init\n",Module.Type);
			Module.Mode0_Handler = &Module10_Mode0_Handler;
			Module.Mode1_Handler = &Module10_Mode1_Handler;
			break;
		default:
			break;
	}
}

/// @brief System initialization
/// @param  None
void System_Init(void)
{
	USART1_Init();
	LED_Init();
  Button_Init();
	//SPI2_Init();
	IMU_Init();
	Module.Mode0_Handler = &Module_None_Mode0_Handler;
	Module.Mode1_Handler = &Module_None_Mode1_Handler;
	Module.Type = Module_Type_0;
	printf("Module_Type_0");
	Module_Init();

}

void Cyberry_Potter_System_Status_Update(void)
{
      switch(Cyberry_Potter.System_Mode){
	      case SYSTEM_MODE_0:
			Cyberry_Potter.System_Mode = SYSTEM_MODE_1;
			#ifdef SERIAL_DEBUG
			printf("SYSTEM_MODE_1\n");
			#endif //SERIAL_DEBUG
			break;
	      case SYSTEM_MODE_1:
			#ifdef LASER_ENABLE
			Cyberry_Potter.System_Mode = SYSTEM_MODE_2;
			#else
			Cyberry_Potter.System_Mode = SYSTEM_MODE_0;
			#endif
			#ifdef SERIAL_DEBUG
			printf("SYSTEM_MODE_0\n");
			#endif //SERIAL_DEBUG
			break;
	      #ifdef LASER_ENABLE
	      case SYSTEM_MODE_2:
			Cyberry_Potter.System_Mode = SYSTEM_MODE_0;
			#ifdef SERIAL_DEBUG
			printf("SYSTEM_MODE_0\n");
			#endif //SERIAL_DEBUG
			break;
	      #endif
      }  
}

/// @brief IMU and IR RF module interrput handler
void EXTI9_5_IRQHandler(void)
{
	static uint8_t i = 0;
	//IMU read
	if(EXTI_GetITStatus(EXTI_Line5)==SET){
		IMU_Get_Data(i);
		i++;
		if(i >= IMU_SEQUENCE_LENGTH_MAX){
			i = 0;
			//printf("Samlpled\n");
			IMU.Sample_Stop();
			#ifdef SYSTEM_MODE_DATA_COLLECT
			Delay_ms(200);
			IMU_Data_Print();
			#endif
		}	
		EXTI_ClearITPendingBit(EXTI_Line5);	
  }
}

void EXTI_Stop(void)
{
	EXTI->IMR &= ~(EXTI_Line0);
}

void EXTI_Restore(void)
{
	EXTI->IMR |= EXTI_Line0;
}
