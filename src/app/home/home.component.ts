import { Component, OnInit, ViewChild, ViewChildren } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatOptionSelectionChange } from '@angular/material/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSelect, MatSelectChange } from '@angular/material/select';
import * as moment from 'moment';
import { BackendService } from '../backend.service';
import { config } from '../config';
import { ConfirmPopupComponent } from '../confirm-popup/confirm-popup.component';
import { MessageService } from '../message.service';
import { UserModel } from '../models/userModel';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {  
  moment: any = moment
  user: UserModel
  groups: Array<any> = []
  groupForm: FormGroup
  groupsLoading: boolean = false
  currGroup: any = null

  constructor(
    private backendService: BackendService,
    private messageService: MessageService,
    public dialog: MatDialog,
    private fb: FormBuilder
  ) { }

  ngOnInit(): void {
    this.backendService.getUser().toPromise().then((data: any) => {
      if (data?.id) {
        this.user = data
      }
    }).catch(() => {
      this.messageService.open("There was an error while trying to get the logged in user.")
    })

    this.groupForm = this.fb.group({ group: [null] })
  }

  signOut() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Sign Out",
        message: `Are you sure you want to sign out?<br>(Signed in as ${this.user.name}).`,
        primaryButton: "Confirm"
      }
    })

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        window.location.href = config.api_root + '/logout'
      }
    })
  }

  signIn() {
    window.location.href = config.api_root + "/login"
  }

  selectGroup(event: MatSelectChange) {
    this.backendService.getGroupFromDB(event.value?.id).toPromise().then((data: any) => {
      this.currGroup = event.value
      if (data?.id) {
        this.currGroup['isBotRegistered'] = true
      } else {
        this.currGroup['isBotRegistered'] = false
      }
    })
    
  }

  loadGroups() {
    this.groupsLoading = true
    this.backendService.getGroups(this.user.access_token).toPromise().then((data: any) => {
      this.groups = data.response
    }).catch(() => {
      this.messageService.open("There was an issue getting your groups. Please try again.")
    }).finally(() => { this.groupsLoading = false })
  }

  isGroupAdmin(group: any) {
    return group.members.filter((x: any) => x.user_id == this.user.id)[0].roles.includes("admin")
  }

  addBot() {
    this.backendService.registerBot(this.currGroup.id).toPromise().then((data: any) => {
      this.currGroup['isBotRegistered'] = true
      this.messageService.open(`Successfully added Reminder Bot to ${this.currGroup.name}!`)
    })
  }

  deleteBot() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Delete Bot ",
        message: `Are you sure you want to remove Reminder Bot from ${this.currGroup.name}? You can always re-add the bot.`,
        primaryButton: "Confirm"
      }
    })

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.backendService.deleteBotFromGroup(this.currGroup.id).toPromise().then(() => {
          this.currGroup['isBotRegistered'] = false
          this.messageService.open(`Successfully removed Reminder Bot from ${this.currGroup.name}.`)
        }).catch(() => {
          this.messageService.open("Unable to delete bot. Please try again.")
        })
      }
    })
    
  }

}
