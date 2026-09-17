# Соответствие сценариев и результатов

Это целевые диагностические композиции. Отсутствие Violation не доказывает обязательного завершения при остановке времени или бесконечных переходах без продвижения времени.

| Сценарий | Требование | Точный запрос | Ожидание | Факт | run_id |
|---|---|---|---|---|---|
| old | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | not_available | ack-001-20260916-old |
| old | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | not_available | ack-001-20260916-old |
| old | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-old |
| old | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-old |
| fixed | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | satisfied | not_available | ack-001-20260916-fixed |
| fixed | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | not_available | ack-001-20260916-fixed |
| fixed | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-fixed |
| fixed | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-fixed |
| late_timeout | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | not_available | ack-001-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | not_available | ack-001-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0` | satisfied | not_available | ack-001-20260916-late_timeout |
| late_ack | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | not_available | ack-001-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | not_available | ack-001-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0` | satisfied | not_available | ack-001-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && mac_obs_ack_late && !mac_phy_ack_timeout` | satisfied | not_available | ack-001-20260916-late_ack |
| old | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-002-20260916-old |
| old | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | satisfied | ack-002-20260916-old |
| old | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-old |
| old | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-old |
| fixed | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | satisfied | satisfied | ack-002-20260916-fixed |
| fixed | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | satisfied | ack-002-20260916-fixed |
| fixed | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-fixed |
| fixed | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-fixed |
| late_timeout | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-002-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | satisfied | ack-002-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-late_timeout |
| late_timeout | Историческая проверка; см. README | `E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0` | satisfied | satisfied | ack-002-20260916-late_timeout |
| late_ack | Историческая проверка; см. README | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-002-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> fixture_completed == 2` | satisfied | satisfied | ack-002-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0` | satisfied | satisfied | ack-002-20260916-late_ack |
| late_ack | Историческая проверка; см. README | `E<> mac_A_SCH_0.Idle && mac_obs_ack_late && !mac_phy_ack_timeout` | satisfied | satisfied | ack-002-20260916-late_ack |
| old | Воспроизведение дефекта / отсутствие ложного нарушения / отрицательный контроль | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-review-003-20260917-old |
| old | Достижимость последовательных завершений | `E<> fixture_completed == 2` | satisfied | satisfied | ack-review-003-20260917-old |
| old | Достижимость подтверждения | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-old |
| old | Достижимость тайм-аута | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-old |
| fixed | Воспроизведение дефекта / отсутствие ложного нарушения / отрицательный контроль | `A[] not obs_mac_ObsPhyAck_0.Violation` | satisfied | satisfied | ack-review-003-20260917-fixed |
| fixed | Достижимость последовательных завершений | `E<> fixture_completed == 2` | satisfied | satisfied | ack-review-003-20260917-fixed |
| fixed | Достижимость подтверждения | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-fixed |
| fixed | Достижимость тайм-аута | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-fixed |
| late_timeout | Воспроизведение дефекта / отсутствие ложного нарушения / отрицательный контроль | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-review-003-20260917-late_timeout |
| late_timeout | Достижимость последовательных завершений | `E<> fixture_completed == 2` | satisfied | satisfied | ack-review-003-20260917-late_timeout |
| late_timeout | Достижимость подтверждения | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-late_timeout |
| late_timeout | Достижимость тайм-аута | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-late_timeout |
| late_timeout | Сохранение просрочки при следующей команде | `E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0` | satisfied | satisfied | ack-review-003-20260917-late_timeout |
| late_ack | Воспроизведение дефекта / отсутствие ложного нарушения / отрицательный контроль | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-review-003-20260917-late_ack |
| late_ack | Достижимость последовательных завершений | `E<> fixture_completed == 2` | satisfied | satisfied | ack-review-003-20260917-late_ack |
| late_ack | Достижимость подтверждения | `E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-late_ack |
| late_ack | Достижимость тайм-аута | `E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-late_ack |
| late_ack | Сохранение просрочки при следующей команде | `E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0` | satisfied | satisfied | ack-review-003-20260917-late_ack |
| late_ack | Достижимость позднего подтверждения | `E<> mac_A_SCH_0.Idle && mac_obs_ack_late && !mac_phy_ack_timeout` | satisfied | satisfied | ack-review-003-20260917-late_ack |
| no_completion | Отправка первой команды достижима | `E<> fixture_sent == 1 && mac_obs_ack_active` | satisfied | satisfied | ack-review-003-20260917-no_completion |
| no_completion | Нарушение без любого завершения | `E<> obs_mac_ObsPhyAck_0.Violation && fixture_sent == 1 && fixture_completed == 0 && mac_A_SCH_0.WaitPHYAck && mac_obs_ack_active && mac_c_obs_ack > 3` | satisfied | satisfied | ack-review-003-20260917-no_completion |
| no_completion | Завершение исключено в отрицательном сценарии | `A[] fixture_completed == 0` | satisfied | satisfied | ack-review-003-20260917-no_completion |
| no_completion | Отрицательный контроль без завершения | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-review-003-20260917-no_completion |
| zero_time | Отправка достижима | `E<> fixture_sent == 1 && mac_obs_ack_active && fixture_from_first_send == 0` | satisfied | satisfied | ack-review-003-20260917-zero_time |
| zero_time | Отправка и ACK первой команды в один момент | `E<> fixture_sent == 1 && fixture_completed == 1 && !mac_obs_ack_active && !mac_phy_ack_timeout && fixture_from_first_send == 0` | satisfied | satisfied | ack-review-003-20260917-zero_time |
| zero_time | Завершение и следующая отправка в один момент | `E<> fixture_sent == 2 && fixture_completed == 1 && mac_obs_ack_active && fixture_from_completion == 0` | satisfied | satisfied | ack-review-003-20260917-zero_time |
| zero_time | Две отдельные команды без продвижения времени | `E<> fixture_sent == 2 && fixture_completed == 2 && fixture_from_first_send == 0` | satisfied | satisfied | ack-review-003-20260917-zero_time |
| zero_time | Отсутствие ложного нарушения / отрицательный контроль | `A[] not obs_mac_ObsPhyAck_0.Violation` | satisfied | satisfied | ack-review-003-20260917-zero_time |
| late_then_zero | Отправка достижима | `E<> fixture_sent == 1 && mac_obs_ack_active && fixture_from_first_send == 0` | satisfied | satisfied | ack-review-003-20260917-late_then_zero |
| late_then_zero | Отправка и ACK первой команды в один момент | `E<> fixture_sent == 1 && fixture_completed == 1 && !mac_obs_ack_active && !mac_phy_ack_timeout && fixture_from_first_send == 0` | satisfied | satisfied | ack-review-003-20260917-late_then_zero |
| late_then_zero | Завершение и следующая отправка в один момент | `E<> fixture_sent == 2 && fixture_completed == 1 && mac_obs_ack_active && fixture_from_completion == 0` | satisfied | satisfied | ack-review-003-20260917-late_then_zero |
| late_then_zero | Две отдельные команды без продвижения времени | `E<> fixture_sent == 2 && fixture_completed == 2 && fixture_from_first_send == 0` | satisfied | satisfied | ack-review-003-20260917-late_then_zero |
| late_then_zero | Отсутствие ложного нарушения / отрицательный контроль | `A[] not obs_mac_ObsPhyAck_0.Violation` | NOT satisfied | NOT satisfied | ack-review-003-20260917-late_then_zero |
| late_then_zero | Просрочка первой команды сохранена при немедленной следующей отправке | `E<> fixture_sent == 2 && fixture_completed == 1 && mac_obs_ack_active && mac_obs_ack_late && fixture_from_completion == 0` | satisfied | satisfied | ack-review-003-20260917-late_then_zero |
