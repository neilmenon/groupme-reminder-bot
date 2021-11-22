import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { config } from './config';

@Injectable({
  providedIn: 'root'
})
export class BackendService {

  constructor(
    private http: HttpClient
  ) { }

  getUser() {
    return this.http.get(config.api_root + "/user")
  }

  getGroups(accessToken: string) {
    return this.http.get(`https://api.groupme.com/v3/groups?token=${accessToken}`)
  }

  registerBot(groupId: any) {
    return this.http.post(config.api_root + "/register-bot", { group_id: groupId })
  }

  getGroupFromDB(groupId: any) {
    return this.http.get(config.api_root + "/groups/" + groupId)
  }

  deleteBotFromGroup(groupId: any) {
    return this.http.delete(config.api_root + "/groups/" + groupId + "/delete")
  }

  createReminder(groupId: any, text: string, timestamp: number, frequency: number) {
    return this.http.post(config.api_root + "/reminders/create", {
      group_id: groupId,
      text: text,
      timestamp: timestamp,
      frequency: frequency,
    })
  }

  getReminders(groupId: any, sortBy: string = "timestamp", sortOrder: string = "DESC") {
    return this.http.post(config.api_root + "/reminders/get", {
      group_id: groupId,
      sort_by: sortBy,
      sort_order: sortOrder
    })
  }

  deleteReminder(groupId: any, reminderId: number) {
    return this.http.post(config.api_root + "/reminders/delete", { group_id: groupId, reminder_id: reminderId })
  }
}
