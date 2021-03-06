/*
 * Copyright 2015 Matthias Einwag
 *
 * The jawampa authors license this file to you under the Apache License,
 * version 2.0 (the "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at:
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

package ws.wamp.jawampa.connection;

/**
 * A listener interface for a connection that is currently established.<br>
 * Once the connection is established one of the callback methods that this
 * listener provides will be called.
 */
public interface IPendingWampConnectionListener {
    /** The connection succeeded */
    void connectSucceeded(IWampConnection connection);
    
    /**
     * The connection of the transport failed or the connection was cancelled.
     */
    void connectFailed(Throwable cause);
}
