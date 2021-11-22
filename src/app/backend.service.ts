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
}
