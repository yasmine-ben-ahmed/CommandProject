import { Component } from '@angular/core';
import { UploadComponent } from './upload/upload.component'; // Import UploadComponent

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [UploadComponent],  // Add UploadComponent here
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'shape-to-command';
}
