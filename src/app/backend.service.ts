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
}
